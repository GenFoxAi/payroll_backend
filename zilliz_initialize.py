import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Milvus
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set it in your .env file.")

ZILLIZ_CLOUD_URI = os.getenv("ZILLIZ_CLOUD_URI")
ZILLIZ_CLOUD_API_KEY = os.getenv("ZILLIZ_CLOUD_API_KEY")
if not ZILLIZ_CLOUD_URI or not ZILLIZ_CLOUD_API_KEY:
    raise ValueError("Zilliz Cloud credentials not found. Please set them in your .env file.")

def load_documents(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


file_path = 'policies.txt'
document_text = load_documents(file_path)
docs = [Document(page_content=document_text)]

embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=0)
split_docs = text_splitter.split_documents(docs)

vector_store = Milvus.from_documents(
    documents=split_docs,
    embedding=embedding,
    connection_args={
        "uri": ZILLIZ_CLOUD_URI,
        "token": ZILLIZ_CLOUD_API_KEY,
        "secure": True,
    },
    collection_name="payroll_collection",
)

retriever = vector_store.as_retriever()

print("Documents have been successfully embedded and stored in Zilliz Cloud.")
