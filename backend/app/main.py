from fastapi import FastAPI
from app.api import router

app = FastAPI()
app.include_router(router)
#六个功能分别在 api.py 和 langchain_service.py 中添加接口和实现逻辑