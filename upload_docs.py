from openai import OpenAI
from qdrant_client import QdrantClient
import time
import utils
import processing_docs

##################################### MAIN #####################################
## MAIN SET UP 
config = utils.load_config('config.yaml')

# Initialize Qdrant client with the host and port
client_vdb = QdrantClient(config['qdrant']['host'], port=config['qdrant']['port'])

# Initialize OpenAI client with your API key
client_ia = OpenAI(api_key=config['openai']['key'])
## PROCESSING OF THE FIRST STEP OF THE API

# Set the file path of the document
# file_path = r'C:\Users\fcoy\Documents\Personal_Docs\AI_Engineer_test\AI_Engineer_Test_Django\all-docs\Documentacion proceso Extraccion CVs.docx'
file_path = r'C:\Users\fcoy\Documents\Personal_Docs\AI_Engineer_test\AI_Engineer_Test_Django\all-docs\test.docx'
# file_path = r'C:\Users\fcoy\Documents\Personal_Docs\AI_Engineer_test\AI_Engineer_Test_Django\all-docs\UNICEF_AUTODETECTION_POSSIBLE_VIOLIATION_REPORTS.docx'

# Measure the execution time
start_time = time.time()

# Create embeddings for the document
embeddings, num_tokens, text = processing_docs.create_embeddings(client_ia, file_path,config['openai']['tokenizer'], config['openai']['model'])
outcome_upload = processing_docs.upload_documents(config['qdrant']['collection'], client_vdb, embeddings, text, id=0)  ## INSERT ID GETTING DIRECTLY TO API CALL 
print(outcome_upload)
end_time = time.time()
duration = end_time - start_time
# Print the duration
print("Cell Run Time:", duration)


##### PROCESSING OF THE SECOND STEP OF THE API
prompt = "How can I create a machine leaning model for UNICEF?"
response = processing_docs.get_answer_llm(config, client_vdb, client_ia, prompt)
print(response)
