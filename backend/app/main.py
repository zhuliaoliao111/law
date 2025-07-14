from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .services.smart_contracts import router as smart_contracts_router
from .api import router
#git add .
#git commit -m "XXXXX"
#git push -u origin master

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
