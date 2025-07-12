from fastapi import APIRouter, Body
from app.services.langchain_service import ai_legal_qa_function
from typing import Optional

router = APIRouter()

@router.get("/feature1")
def feature1():
    # 调用 langchain_service 的功能
    return some_langchain_function()

@router.post("/ai_legal_qa")
def ai_legal_qa(
    question: str = Body(..., embed=True),
    model: str = Body('gpt-3.5', embed=True),
    session_id: Optional[str] = Body(None, embed=True)
):
    """
    AI懂法接口，支持多模型、多轮对话
    """
    return ai_legal_qa_function(question, model, session_id)

@router.get("/ai_legal_history/{session_id}")
def get_ai_legal_history(session_id: str):
    from app.services.langchain_service import get_history
    return get_history(session_id)