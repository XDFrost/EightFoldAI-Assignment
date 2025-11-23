from app.api.websocket import router as websocket_router
from fastapi.middleware.cors import CORSMiddleware
from app.utils.lifespanUtil import lifespan
from app.Config.dataConfig import Config
from dotenv import load_dotenv
from fastapi import FastAPI

mainAppCfg=Config.MainAppConfig()
load_dotenv()

app = FastAPI(
    title=mainAppCfg.TITLE, 
    version=mainAppCfg.VERSION, 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=mainAppCfg.ALLOWORIGINS,  
    allow_credentials=mainAppCfg.ALLOWCREDENTIALS,
    allow_methods=mainAppCfg.ALLOWMETHODS,  
    allow_headers=mainAppCfg.ALLOWHEADERS,  
)

app.include_router(
    websocket_router, 
    prefix=mainAppCfg.SOCKETCHATPREFIX
)
