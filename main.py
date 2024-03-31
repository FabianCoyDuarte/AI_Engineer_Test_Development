from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status, Path, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from qdrant_client import QdrantClient
from fastapi.responses import JSONResponse
from typing import Optional
import security.security as security
import lib.processing_docs as processing_docs
import lib.utils as utils
from docx import Document
import io

# Load the configuration file
config = utils.load_config('./config.yaml')

# Load documentation of the API development and show the information when is deployed
tag = utils.load_json(r'./data/tags.json') 
tags = [tag[t] for t in tag]

# Initialize Qdrant client with the host and port according to the configuration file
client_vdb = QdrantClient(config['qdrant']['host'], port=config['qdrant']['port'])

# Initialize OpenAI client with your API key according to the configuration file
client_ia = OpenAI(api_key=config['openai']['key'])

# Create a FastAPI instance with the title and tags
app = FastAPI(title="AI Engineer Test to create", openapi_tags= tags)

origins = ["*"]

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Route for the home page
@app.get("/", tags=["Home"])
async def home():
    """
    Check if the API is running correctly.

    Returns:
        dict: A dictionary indicating that the API is running correctly.
    """
    return {'API created by Fabian Coy -2024 AI Engineer Test': 'API to load, upload data to QDRANT and get answers from OpenAI'}

# Route for uploading a .docx file
@app.post("/upload/", tags=["Upload_file"])
async def upload_file(file: UploadFile = File(...), id: Optional[int] = 0, current_user: security.User = Depends(security.get_current_active_user)):
    """
    Upload or update a document in Qdrant vector database.

    Args:
        file (UploadFile): The .docx file to be uploaded.
        id (Optional[int]): The ID of the document (default is 0) when the function is upload a new document. If you want to update a document, you need to provide the ID of the document.
        current_user (security.User): The current authenticated user.

    Returns:
        JSONResponse: A JSON response indicating the status of the upload process.
    """
    # check if the file is a .docx file 
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file")
    # check if the ID is valid
    if id != 0:    
        information = client_vdb.get_collection(collection_name=config['qdrant']['collection'])
        last_id = information.vectors_count
        if id > last_id:
            raise HTTPException(status_code=400, detail=f"Invalid ID. The last ID is {last_id}")

    # read the contents of the file, create embeddings, and upload the document to Qdrant
    try:
        contents = await file.read()
        doc = Document(io.BytesIO(contents))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        embeddings, _, _ = processing_docs.create_embeddings(client_ia, text, config['openai']['tokenizer'], config['openai']['model'])
        outcome_upload = processing_docs.upload_documents(config['qdrant']['collection'], client_vdb, embeddings, text, id=id)

    except Exception:
        raise HTTPException(status_code=500, detail=f"Error processing file: {file.filename}")
    # return the filename and the status of the upload process
    return JSONResponse(content={"the filename": file.filename, "process created": outcome_upload}, status_code=200)

# Route to search the best document based on the prompt and create an answer using LLM model 
@app.get("/search/{prompt}", tags=["Search"])
async def read_words(prompt: str = Path(..., max_length=config['api']['max_length_prompt']), current_user: security.User = Depends(security.get_current_active_user)):
    """
    Search for words or phrases in the documents stored in Qdrant vector database.

    Args:
        prompt (str): The search prompt or query.
        current_user (security.User): The current authenticated user.

    Returns:
        JSONResponse: A JSON response indicating the LLM outcome using the prompt and document.
    """
    response = processing_docs.get_answer_llm(config, client_vdb, client_ia, prompt)
    return JSONResponse(content={"LLM answer": response}, status_code=200)

# Route to generate a token for accessing the API securely
@app.post("/token", response_model=security.Token, tags=["Generate Token"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Generate a token for accessing the API securely.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the username and password.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = security.authenticate_user(security.db_dummy, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config['secure']['ACCESS_TOKEN_EXPIRE_MINUTES'])
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
