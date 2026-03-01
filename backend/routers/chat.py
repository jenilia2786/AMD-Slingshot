from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from services.crew_ai_service import _execution_lock
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

router = APIRouter(prefix="/api/chat", tags=["Support Chat"])

class ChatMessage(BaseModel):
    text: str
    role: str # 'user' or 'bot'

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/send")
async def chat_with_agent(req: ChatRequest):
    """Real AI Chat Support using direct LLM calls for speed"""
    async with _execution_lock:
        try:
            llm = ChatOllama(model="llama3", base_url="http://localhost:11434", temperature=0.7)
            
            # Simple context preparation
            context_str = ""
            if req.history:
                # Last 5 messages for context
                recent_history = req.history[-5:]
                context_str = "\n".join([f"{m.role}: {m.text}" for m in recent_history])

            system_prompt = """You are AccelerateAI Support Guide.
Friendly, knowledgeable, and dedicated to the Global student community. 
Expert in the Slingshot Talent ecosystem.
Help students navigate the portal, explain rewards, and provide technical guidance.
Keep messages concise and encouraging."""

            user_prompt = f"Chat History:\n{context_str}\n\nStudent's New Message: {req.message}\nHelpful Support Guide Response:"

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=30
            )

            return {"reply": response.content.strip()}
            
        except Exception as e:
            print(f"❌ Chat AI Error: {e}")
            return {"reply": "I'm having trouble connecting right now. Please try again or head to the Support section!"}
