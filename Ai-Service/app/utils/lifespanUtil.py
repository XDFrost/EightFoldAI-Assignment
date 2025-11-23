from app.db.supabase_client import get_supabase_client
from pinecone import PineconeAsyncio, ServerlessSpec
from app.Config.queryConfig import QueryConfig
from app.states.global_state import services
from contextlib import asynccontextmanager
from app.api.websocket import orchestrator
from app.Config.dataConfig import Config
from app.utils.logger import logger
from fastapi import FastAPI
import psycopg2
import asyncio

settings = Config.Config.from_env()
queries = QueryConfig.SupabaseQueries()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    """
    
    logger.info("Executing startup checks...")
    
    # Supabase Setup
    try:
        logger.info("Checking for required tables...")
        conn = psycopg2.connect(settings.DATABASE_URL)
        cursor = conn.cursor()
        
        required_tables = settings.SupabaseTables
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(queries.checkIfTableExists, (table,))
            if not cursor.fetchone()[0]:
                missing_tables.append(table)
        
        if missing_tables:
            logger.info(f"Missing tables: {missing_tables}. Running migration...")
            cursor.execute(queries.getCreateTablesSQL)
            conn.commit()
            logger.info("Tables created successfully.")
        else:
            logger.info("All required tables exist.")
            
        cursor.close()
        conn.close()
        
        # Initialize supabase
        supabase = await get_supabase_client()
        services.set_supabase(supabase)
        logger.info("Supabase client initialized.")
        
    except Exception as e:
        logger.error(f"Startup DB check failed: {e}")
    
    # Pinecone Setup
    pc = None
    if settings.PINECONE_API_KEY:
        try:
            logger.info("Initializing Pinecone...")
            pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
            services.set_pinecone(pc)
            
            index_name = settings.PINECONE_INDEX
            existing_indexes = await pc.list_indexes()
            existing_names = [i.name for i in existing_indexes]
            
            if index_name not in existing_names:
                logger.info(f"Creating Pinecone index '{index_name}'...")
                await pc.create_index(
                    name=index_name,
                    dimension=settings.PineconeDimensions, 
                    metric=settings.PineconeMetric,
                    spec=ServerlessSpec(
                        cloud=settings.PineconeCloud,
                        region=settings.PineconeRegion
                    )
                )
                
                while True:
                    desc = await pc.describe_index(index_name)
                    if desc.status['ready']:
                        break
                    await asyncio.sleep(1)
                logger.info("Pinecone index created and ready.")
            else:
                logger.info(f"Pinecone index '{index_name}' exists.")
                
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {e}")
    else:
        logger.warning("PINECONE_API_KEY not set. RAG disabled.")

    yield
    
    logger.info("Shutting down...")
    
    # Close processes
    if orchestrator:
        await orchestrator.aclose()
        logger.info("Orchestrator shutdown complete.")

    if pc:
        await pc.close()
        logger.info("Pinecone connection closed.")
