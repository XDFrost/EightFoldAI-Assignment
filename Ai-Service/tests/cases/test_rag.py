import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.knowledge_base import KnowledgeBaseService
from app.Config.dataConfig import Config

settings = Config.Config.from_env()

from pinecone import PineconeAsyncio
from app.states.global_state import services

async def test_rag():
    print("Testing RAG...")
    
    # Initialize Global State for Test
    if not settings.PINECONE_API_KEY:
        print("❌ Pinecone API Key not set.")
        return
        
    pc = PineconeAsyncio(api_key=settings.PINECONE_API_KEY)
    services.set_pinecone(pc)
    
    try:
        kb = KnowledgeBaseService()

        company = "TestCorp"
        content = "TestCorp is a leading provider of widgets. They were founded in 2020."
        
        print(f"Storing research for {company}...")
        await kb.store_research(company, content)
        
        # Wait for indexing (Pinecone is usually fast but eventual consistency)
        print("Waiting for indexing...")
        await asyncio.sleep(5)
        
        query = "What does TestCorp do?"
        print(f"Searching for: '{query}'")
        results = await kb.search(query, company=company)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for res in results:
                print(f" - {res}")
        else:
            print("❌ No results found (might be due to high threshold).")
            
        # Test irrelevant query
        query = "What is the capital of France?"
        print(f"Searching for irrelevant query: '{query}'")
        results = await kb.search(query, company=company)
        if not results:
            print("✅ Correctly filtered out irrelevant results.")
        else:
            print(f"⚠️ Found results for irrelevant query (threshold might be too low): {results}")
            
    finally:
        await pc.close()

if __name__ == "__main__":
    asyncio.run(test_rag())
