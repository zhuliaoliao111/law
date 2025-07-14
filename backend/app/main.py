from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services.smart_contracts import router as smart_contracts_router
from .api import router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)
app.include_router(router)
app.include_router(smart_contracts_router)
#六个功能分别在 api.py 和 languvichain_service.py 中添加接口和实现逻辑