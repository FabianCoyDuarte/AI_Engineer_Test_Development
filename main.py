from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status, Path, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from qdrant_client import QdrantClient
from fastapi.responses import JSONResponse
from typing import Optional
import security
import processing_docs
import utils
from docx import Document
import io


# Load the configuration file
config = utils.load_config('config.yaml')
tag = utils.load_json('tags.json') 
tags = [tag[t] for t in tag]
# print(tags)
JWT_SECRET = config['secure']['SECRET_KEY']

# Initialize Qdrant client with the host and port
client_vdb = QdrantClient(config['qdrant']['host'], port=config['qdrant']['port'])

# Initialize OpenAI client with your API key
client_ia = OpenAI(api_key=config['openai']['key'])


app = FastAPI(title="AI Engineer Test to create", openapi_tags= tags)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Home"])
async def home():
        return {'API created by Fabian Coy -2024 AI Engineer Test': 'API to load, upload data to QDRANT and get answers from OpenAI'}

# Route for uploading a .docx file
@app.post("/upload/", tags=["Upload_file"])
async def upload_file(file: UploadFile = File(...), id: Optional[int] = 0, current_user: security.User = Depends(security.get_current_active_user)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file")

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

    return JSONResponse(content={"the filename": file.filename, "process created": outcome_upload}, status_code=200)

@app.get("/search/{prompt}", tags=["Search"])
async def read_words(prompt: str = Path(..., max_length=config['api']['max_length_prompt']), current_user: security.User = Depends(security.get_current_active_user)):
    response = processing_docs.get_answer_llm(config, client_vdb, client_ia, prompt)
    return {'response': response}

@app.post("/token", response_model=security.Token, tags=["Generate Token"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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
