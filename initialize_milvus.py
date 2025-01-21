import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Milvus
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from pymilvus import connections

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set it in your .env file.")

def load_documents(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

file_path = 'policies.txt' 
document_text = load_documents(file_path)

docs = [Document(page_content=document_text)]

embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)
split_docs = text_splitter.split_documents(docs)

# connections.connect(host='localhost', port='19530') 

vector_store = Milvus.from_documents(
    documents=split_docs,
    collection_name="payroll_collection",  
    embedding=embedding,
)

retriever = vector_store.as_retriever()

print("Documents have been successfully embedded and stored in Milvus.")
