from person import Person
import gradio as gr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from app_tools import chat, in_memory_chat_history, session_data
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str
    is_end: bool = False

class ChatResponse(BaseModel):
    session_id: str
    bot_response: str


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_handler(req: ChatRequest):
 
    me = Person()
    session_id = req.session_id
    if req.is_end:
        print(in_memory_chat_history[session_id]["questions"])
        print( (not in_memory_chat_history[session_id]["email"]) or in_memory_chat_history[session_id]["questions"])
        if (not in_memory_chat_history[session_id]["email"]) or in_memory_chat_history[session_id]["questions"]:
            me.send_email(in_memory_chat_history[session_id])

        if in_memory_chat_history[session_id]["email"]:
            me.email(in_memory_chat_history[session_id])

   
    if not session_id: 
        session_id = str(uuid.uuid4())
        in_memory_chat_history[session_id] = session_data


    session = in_memory_chat_history[session_id]
    result = chat(me.chat,session["history"],req.user_message,session_id)
    print(session["email"], session["questions"])
    return ChatResponse(
        session_id= session_id,
        bot_response=result
    )
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
   
