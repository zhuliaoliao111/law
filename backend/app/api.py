from fastapi import APIRouter
from app.services.langchain_service import some_langchain_function

router = APIRouter()

@router.get("/feature1")
def feature1():
    # 调用 langchain_service 的功能
    return some_langchain_function()