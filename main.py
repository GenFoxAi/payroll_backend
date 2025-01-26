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

memory_store={}
@app.post("/chat/")
async def chat(state: State, request: Request):
    try:
        session_id = request.headers.get("session-id", "default-session")
        if session_id not in memory_store:
            memory_store[session_id] = {"messages": []}
            
        memory_store[session_id]["messages"].extend(state.messages)
        user_query = state.messages[-1].content.strip().lower()
        employee_id = "E001" 
        user_data = fetch_user_data(employee_id)

        if "apply for leave" in user_query or "leave application" in user_query or "apply leave" in user_query or "apply for a leave" in user_query or ("apply" in user_query and "leave" in user_query):
            ai_message = {
                "role": "assistant",
                "content": f"To apply for leave, please click here to open the leave application. "
            }
            new_messages = state.messages + [ai_message]
            return {"messages": new_messages, "conversation_state": state.conversation_state}
        
        if "submit reimbursement" in user_query or "reimbursement request" in user_query or "apply for reimbursement" in user_query or "request expense reimbursement" in user_query or "submit a reimbursement" in user_query or "apply for a reimbursement" in user_query or("apply" in user_query and "reimbursement" in user_query) or ("submit" in user_query and "reimbursement" in user_query):
            ai_message = {
                "role": "assistant",
                "content": f"To submit a reimbursement request, please click here to open the reimbursement submission."
            }
            new_messages = state.messages + [ai_message]
            return {"messages": new_messages, "conversation_state": state.conversation_state}

       

        retrieved_docs = vector_store.similarity_search(user_query)
        if not retrieved_docs:
            ai_message = {
                "role": "assistant",
                "content": "<b>Sorry, I couldn't find any relevant information</b> related to your query. Please provide more details or contact HR for further assistance."
            }
            new_messages = state.messages + [ai_message]
            memory_store[session_id]["messages"] = new_messages
            return {"messages": new_messages, "conversation_state": state.conversation_state}
        policy_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        conversation_history = "\n".join(
            [f"{msg.role.capitalize()}: {msg.content}" for msg in state.messages]
        )

        prompt = f"""
        You are a smart assistant with access to employee payroll data, Saudi labor policies, and prior conversation history.

        Conversation History:
        {conversation_history}

        Employee Data:
        {user_data}

        Relevant Policies and Formulas:
        {policy_context}

        User Query:
        "{user_query}"

        **Updated Instructions**:
        1. If the user is talking in arabic language then give the responses in arabic language only.
        2. **Conversation History First**: Start by checking the conversation history to determine if the query can be answered based on previous interactions.  
           - If relevant information is found, use it to craft a clear response without explicitly mentioning the conversation history unless absolutely necessary.  
           - For casual or unrelated queries, respond directly without referencing conversation history.  

        3. **Fallback to User Data and Policies**: If the answer is not found in the conversation history, use the provided employee data and policies to interpret and address the query.  

        4. **Query-Specific Responses**:  
        - For **calculation-based queries** (e.g., overtime pay, leave balance), perform required calculations and provide clear results.  
        - For **policy-related queries**, provide a **detailed explanation** of the relevant policies, including context, applications, and implications, formatted for clarity.  
        - For **data-related queries**, share only up to the employee's basic salary unless otherwise specified.  
        - For **apply leave-related queries**, guide the user to start the process by typing "apply leave" or related keywords.  
        - For **apply reimbursement-related queries**, guide the user to start the process by typing "apply reimbursement" or related keywords.  

        5. Use proper **Markdown formatting** (e.g., **bold**, _italics_, links, line breaks) in your response to improve readability.  

        6. Share only the **most relevant details**, avoiding unnecessary information or excessive detail.  

        7. All currency-related calculations should be in **SAR (Saudi Riyal)**.  

        8. If the query is unrelated to employee payroll or Saudi labor policies, politely state that it is out of scope.  

        9. Avoid generating responses without appropriate Markdown formatting.

        **Answer Format**:
        - Ensure the response is **clear, concise, and well-structured**.  
        - Only refer to conversation history if it is directly relevant to the user query.  
        - Respond directly and crisply to the query     without unnecessary or redundant phrases.  
        """

        llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo", temperature=0.9)


        response_content = await llm.apredict(prompt)
        

        if not response_content.strip():
            ai_message = {
                "role": "assistant",
                "content": "<b>Sorry, I couldn't generate a response</b> based on your query. Please contact HR or try rephrasing your question."
            }
        else:
            ai_message = {"role": "assistant", "content": response_content}

        
        new_messages = memory_store[session_id]["messages"] + [ai_message]
        memory_store[session_id]["messages"] = new_messages
        return {"messages": new_messages, "conversation_state": state.conversation_state}

    except Exception as e:
        error_message = {
            "role": "assistant",
            "content": f"<b>An error occurred:</b> {str(e)}"
        }
        new_messages = state.messages + [error_message]
        return {"messages": new_messages, "conversation_state": state.conversation_state}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)






   
    


  