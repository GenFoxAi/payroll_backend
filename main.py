import os
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
ZILLIZ_CLOUD_URI = os.getenv("ZILLIZ_CLOUD_URI")     
ZILLIZ_CLOUD_TOKEN = os.getenv("ZILLIZ_CLOUD_API_KEY")  

client = MongoClient(MONGO_URI)
db = client["employee_db"]  

embedding = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vector_store = Milvus(
    embedding_function=embedding,
    collection_name="payroll_collection",
    connection_args={
        "uri": ZILLIZ_CLOUD_URI,
        "token": ZILLIZ_CLOUD_TOKEN,
        "secure": True
    }
)

if not vector_store.client.has_collection("payroll_collection"):
    raise ValueError("Collection 'payroll_collection' not found in Zilliz Cloud.")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://0.0.0.0:5000",
        "http://localhost:5173",
        "https://comm-it-engage-prototype.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str

class State(BaseModel):
    messages: List[Message]
    conversation_state: Optional[Dict] = {}

def fetch_user_data(employee_id: str):
    user_data = {
        "basic_info": db["basic_info"].find_one({"employeeId": employee_id}),
        "employment_details": db["employment_details"].find_one({"employeeId": employee_id}),
        "payroll": db["payroll"].find_one({"employeeId": employee_id}),
        "leaves": db["leaves"].find_one({"employeeId": employee_id}),
        "reimbursement_claims": db["reimbursement_claims"].find_one({"employeeId": employee_id}),
        "attendance": db["attendance"].find_one({"employeeId": employee_id}),
        "roles": db["roles"].find_one({"employeeId": employee_id}),
        "documents": db["documents"].find_one({"employeeId": employee_id}),
        "gosi": db["gosi"].find_one({"employeeId": employee_id}),
    }

    if not any(user_data.values()):
        raise HTTPException(status_code=404, detail=f"Employee with ID {employee_id} not found.")

    for key in user_data.keys():
        if user_data[key]:
            user_data[key].pop("_id", None)

    return user_data
@app.get("/")
def read_root():
    return {"message": "Welcome to Payroll Backend"}
@app.post("/chat/")
async def chat(state: State, request: Request):
    try:
        user_query = state.messages[-1].content.strip().lower()
        employee_id = "E001" 

        if "apply for leave" == user_query or "leave application" == user_query:
            ai_message = {
                "role": "assistant",
                "content": f"To apply for leave, please click here to open the leave application. "
            }
            new_messages = state.messages + [ai_message]
            return {"messages": new_messages, "conversation_state": state.conversation_state}
        
        if "submit reimbursement" == user_query or "reimbursement request" == user_query or "apply for reimbursement" == user_query or "request expense reimbursement" == user_query:
            ai_message = {
                "role": "assistant",
                "content": f"To submit a reimbursement request, please click here to open the reimbursement submission."
            }
            new_messages = state.messages + [ai_message]
            return {"messages": new_messages, "conversation_state": state.conversation_state}

        user_data = fetch_user_data(employee_id)

        retrieved_docs = vector_store.similarity_search(user_query)
        if not retrieved_docs:
            ai_message = {
                "role": "assistant",
                "content": "<b>Sorry, I couldn't find any relevant information</b> related to your query. Please provide more details or contact HR for further assistance."
            }
            new_messages = state.messages + [ai_message]
            return {"messages": new_messages, "conversation_state": state.conversation_state}
        policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        prompt = f"""
        You are a smart assistant with access to employee payroll data and Saudi labor policies.

        Employee Data:
        {user_data}

        Relevant Policies and Formulas:
        {policy_context}

        User Query:
        "{user_query}"

        Instructions:
        1. Interpret the user's query using the employee data and policies provided.
        2. Perform any required calculations (e.g., overtime pay, leave balance) and provide only key results.
        3. Respond with concise, to-the-point answers that are easy to understand.
        4. Use proper HTML formatting (e.g., <b>, <i>, <u>, <br>) in your response to improve readability.
        5. Share only the most relevant details for the query, avoiding unnecessary information or overly detailed explanations.
        7. If the employee asks for showing all the employee details , only show till the basic salary of the employee.
        6. All currency-related calculations should be in SAR (Saudi Riyal).
        7. If the query is unrelated, politely state that it is out of scope.
        8. Do not return a response without HTML formatting.

        Answer:
        """

        llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo", temperature=0.9)
        response_content = await llm.apredict(prompt)
        print(response_content)

        if not response_content.strip():
            ai_message = {
                "role": "assistant",
                "content": "<b>Sorry, I couldn't generate a response</b> based on your query. Please contact HR or try rephrasing your question."
            }
        else:
            ai_message = {"role": "assistant", "content": response_content}

        ai_message = {"role": "assistant", "content": response_content}
        new_messages = state.messages + [ai_message]
        return {"messages": new_messages, "conversation_state": state.conversation_state}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
