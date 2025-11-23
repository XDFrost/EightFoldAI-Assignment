from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.states.global_state import services
from app.Config.dataConfig import Config
from app.utils.logger import logger
from typing import List
import uuid

settings = Config.Config.from_env()

class KnowledgeBaseService:
    def __init__(self):
        self.index_name = settings.PINECONE_INDEX
        self.embeddings = GoogleGenerativeAIEmbeddings(model=settings.EmbeddingModel)

    async def _get_index(self):
        try:
            pc = services.get_pinecone()
            # Index host
            desc = await pc.describe_index(self.index_name)
            host = desc.host
            return pc.IndexAsyncio(host=host)
        except Exception as e:
            logger.error(f"Failed to get Pinecone index: {e}")
            return None

    async def store_research(
        self, 
        company: str, 
        content: str, 
        metadata: dict = None
    ) -> None:
        idx = await self._get_index()
        if not idx:
            return
        
        try:
            # Truncate content to avoid embedding API limit and pinecone metadata limits 
            truncated_content = content[:10000]
            
            vector = await self.embeddings.aembed_query(truncated_content)
            
            full_metadata = {"company": company, "type": "research_summary", "text": truncated_content}
            if metadata:
                full_metadata.update(metadata)
            
            doc_id = str(uuid.uuid4())
            
            await idx.upsert(vectors=[
                {
                    "id": doc_id,
                    "values": vector,
                    "metadata": full_metadata
                }
            ])
            
        except Exception as e:
            logger.error(f"Error storing research in Pinecone: {e}")
        finally:
            pass

    async def search(
        self, 
        query: str, 
        company: str = None, 
        k: int = settings.PineconeSearchK
    ) -> List[str]:
        try:
            pc = services.get_pinecone()
            desc = await pc.describe_index(self.index_name)
            host = desc.host
            
            async with pc.IndexAsyncio(host=host) as idx:
                vector = await self.embeddings.aembed_query(query)
                
                filter_dict = {}
                if company:
                    filter_dict["company"] = company
                    
                results = await idx.query(
                    vector=vector,
                    top_k=k,
                    filter=filter_dict,
                    include_metadata=True
                )
                
                threshold = settings.PineconeThreshold
                filtered_results = []
                
                for match in results.matches:
                    score = match.score
                    text = match.metadata.get("text", "")
                    
                    if score >= threshold:
                        filtered_results.append(text)
                
                return filtered_results
                
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []
        