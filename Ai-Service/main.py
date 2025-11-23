from app.Config.dataConfig import Config
from app.utils.logger import logger
import uvicorn

uvicornCfg = Config.UvicornConfig()

if __name__ == "__main__":
    logger.info("Starting AI Backend Server...")
    uvicorn.run(
        uvicornCfg.APP, 
        host=uvicornCfg.HOST, 
        port=uvicornCfg.PORT, 
        reload=uvicornCfg.RELOAD
    )
