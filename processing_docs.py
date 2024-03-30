import re
import docx2txt
import tiktoken
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

## Methods to use OPENAI API, process text, and create embeddings

def normalize_text(s):
    """
    Normalize the text by removing special characters and multiple spaces.
    
    Args:
        s (str): The input text.
    
    Returns:
        str: The normalized text.
    """
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r". ,", "", s)
    s = s.replace("..", ".")
    s = s.replace(". .", ".")
    s = s.replace("\n", "")
    s = s.replace("#", "")
    s = s.strip()
    
    return s

def create_embeddings(client, file_path, tokenizer, model):
    """
    Create embeddings for a given document file.
    
    Args:
        client (OpenAI): The OpenAI client.
        file_path (str): The path to the document file.
    
    Returns:
        tuple: A tuple containing the embedding, tokens, and normalized text. 
               Returns a string when the file format is invalid.
    """
    if file_path.lower().endswith(".docx"):
        # Read the document file
        text = docx2txt.process(file_path)
        
        # Normalize the text
        normalized_text = normalize_text(text)
        
        # Tokenize the normalized text
        tokenizer = tiktoken.get_encoding(tokenizer)
        tokens = tokenizer.encode(normalized_text)
        
        # Create embeddings using OpenAI client
        embedding = client.embeddings.create(input=normalized_text, model=model).data[0].embedding
        
        return embedding, tokens, normalized_text
    else:
        return "Error: Invalid file format. Only .docx files are supported.", None, None

## Methods to use QDRANT API, create a collection and index a document

def get_all_collections(client_vdb):
    """
    Get all collections in Qdrant.

    Args:
        client_vdb (QdrantClient): The Qdrant client.

    Returns:
        list: A list of collection names.

    Raises:
        Exception: If there is an error fetching collections from Qdrant.
    """
    try:
        collections_list = []
        collections = client_vdb.get_collections()
        for collection in collections:
            for c in list(collection[1]):
                collections_list.append(c.name)
        return collections_list
    except Exception as e:
        print(f"Error fetching collections from Qdrant: {e}")

def upload_documents(collection_name, client_vdb, embeddings, text, id=0):
    """
    Upload or update a document in the Qdrant vector database.

    Args:
        collection_name (str): The name of the collection in Qdrant.
        client_vdb (QdrantClient): The Qdrant client.
        embeddings (list): The embeddings of the document.
        text (str): The text of the document.
        id (int, optional): The ID of the document. Defaults to 0.

    Returns:
        str: A success message indicating the status of the document upload or update.

    Raises:
        Exception: If there is an error during the document upload or update.
    """
    try:
        if collection_name in get_all_collections(client_vdb):
            # Get the information of the collection and the last id
            if id == 0:
                information = client_vdb.get_collection(collection_name=collection_name)
                last_id = information.vectors_count
                client_vdb.upsert(
                    collection_name=collection_name,
                    wait=True,
                    points=[
                        PointStruct(id=last_id+1, vector=embeddings, payload={"Document_text": text})
                    ]
                )
                return "Document upload successful"
            else: 
                client_vdb.upsert(
                    collection_name=collection_name,
                    wait=True,
                    points=[
                        PointStruct(id=id, vector=embeddings, payload={"Document_text": text})
                    ]
                )
                return "Document update successful"
        else:
            # Create a collection with the given name and vector size in Qdrant
            client_vdb.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            # Index a document with the given id, embeddings, and text in the collection
            client_vdb.upsert(
                collection_name=collection_name,
                wait=True,
                points=[
                    PointStruct(id=1, vector=embeddings, payload={"Document_text": text})
                ]
            )
            return "Collection creation and document upload successful"
    except Exception as e:
        raise Exception(f"Error during document upload or update: {e}")

## Methods to use OPENAI API, process text, and get an answer from a Language Model
def get_answer_llm(config, client_vdb, client_ia, prompt):
    """
    Provides an answer from a Language Model (LLM) based on the similarity between the prompt and documents.

    Parameters:
    - config (dict): A dictionary containing configuration settings.
    - client_vdb: The client for interacting with a Vector Database.
    - client_ia: The client for interacting with an Intelligent Assistant.
    - prompt (str): The prompt to be used for generating the answer.

    Returns:
    - response (str): The generated answer from the LLM.
    """
    # Create an instance of the ChatOpenAI class for the Language Model
    llm = ChatOpenAI(temperature=0, openai_api_key=config['openai']['key'], model_name=config['openai']['llm_model'])

    # Normalize the prompt text
    normalized_prompt = normalize_text(prompt)

    # Create embeddings for the normalized prompt using the Intelligent Assistant client
    embedding = client_ia.embeddings.create(input=normalized_prompt, model=config['openai']['model']).data[0].embedding

    # Search for the best matching document in the Vector Database based on the prompt embedding
    best_document = client_vdb.search(
        collection_name=config['qdrant']['collection'], query_vector=embedding, limit=1
    )

    # Get the text of the best matching document
    text = best_document[0].payload['Document_text']

    # Fill the prompt template with the question and the content of the best matching document
    prompt_template = PromptTemplate.from_template(config['llm']['prompt_template'])
    filled_prompt = prompt_template.format(question=normalized_prompt, content=text)

    # Generate the answer from the Language Model using the filled prompt
    response = llm.call_as_llm(filled_prompt)
    return response