from pymilvus import connections, utility, Collection


connections.connect("default", host="localhost", port="19530")


collections = utility.list_collections()

print("Collections and their schemas:")
for collection_name in collections:
   
    collection = Collection(name=collection_name)
 
    schema = collection.schema
    print(f"\nCollection: {collection_name}")
    print(f"Schema: {schema}")
