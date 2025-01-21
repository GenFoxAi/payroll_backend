import os
from dotenv import load_dotenv
from pymilvus import MilvusClient

load_dotenv()

ZILLIZ_CLOUD_URI = os.getenv("ZILLIZ_CLOUD_URI")     
ZILLIZ_CLOUD_TOKEN = os.getenv("ZILLIZ_CLOUD_API_KEY")  

client = MilvusClient(
    uri=ZILLIZ_CLOUD_URI,
    token=ZILLIZ_CLOUD_TOKEN,
    secure=True
)
print("client connected")

collection_name = "payroll_collection"
print("collection created")
if not client.has_collection(collection_name):
    raise ValueError(f"Collection {collection_name} not found in the cluster.")

desc = client.describe_collection(collection_name)
print("Description:", desc)