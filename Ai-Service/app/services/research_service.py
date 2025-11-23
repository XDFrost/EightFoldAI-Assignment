from perplexity import AsyncPerplexity, DefaultAioHttpClient
from app.services.knowledge_base import KnowledgeBaseService
from app.schemas.websocket_messages import StatusUpdate
from app.states.global_state import services
from app.Config.dataConfig import Config
from tavily import AsyncTavilyClient
from app.utils.logger import logger
from typing import Dict, Any

settings = Config.Config.from_env()

class ResearchService:
    """
    Service to handle research operations using Tavily and Perplexity APIs. Also store results in Knowledge Base.
    """
    def __init__(self) -> None:
        self.tavily = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None
        self.perplexity_key = settings.PERPLEXITY_API_KEY
        self.kb = KnowledgeBaseService()

    async def search_tavily(
        self, 
        query: str, 
        send_callback=None
    ) -> Dict[Any, Any]:
        try:
            if send_callback:
                await send_callback(
                    StatusUpdate(
                        payload={"stage": "research", "message": f"Searching Tavily for: {query}..."}
                    )
                )
            
            response = await self.tavily.search(
                query=query, 
                search_depth=settings.TavilySearchDepth
            )
            return response
        except Exception as e:
            logger.error(f"Tavily Exception: {e}")
            return {"error": str(e)}

    async def search_perplexity(
        self, 
        query: str, 
        send_callback=None
    ) -> Dict[Any, Any]:
        try:
            if send_callback:
                await send_callback(
                    StatusUpdate(
                        payload={"stage": "research", "message": f"Querying Perplexity for: {query}..."}
                        )
                    )

            # AsyncPerplexity with context manager
            http_client = DefaultAioHttpClient()
            try:
                async with AsyncPerplexity(api_key=self.perplexity_key, http_client=http_client) as client:
                    search = await client.search.create(
                        query=query,
                        max_results=settings.PerplexityMaxResults
                    )
                    
                    results = []
                    for result in search.results:
                        results.append({
                            "title": getattr(result, "title", "No Title"),
                            "url": getattr(result, "url", ""),
                            "snippet": getattr(result, "snippet", "")
                        })
                    
                    return {"results": results}
            finally:
                if not http_client.is_closed:
                    await http_client.aclose()
            
        except Exception as e:
            logger.error(f"Perplexity Exception: {e}")
            return {"error": str(e)}

    async def research_company(
        self, 
        company_name: str, 
        scope: str = "General", 
        send_callback=None, 
        custom_query: str = None
    ) -> Dict[str, Any]:
        
        tavily_query = custom_query if custom_query else f"Research {company_name} {scope}"
        perplexity_query = custom_query if custom_query else f"Detailed research on {company_name} focusing on {scope}"
        
        tavily_res = await self.search_tavily(tavily_query, send_callback)
        perplexity_res = await self.search_perplexity(perplexity_query, send_callback)
        
        # Store in KB
        if perplexity_res and "results" in perplexity_res:
            try:
                if send_callback:
                    await send_callback(StatusUpdate(payload={"stage": "research", "message": "Storing research in Knowledge Base..."}))
                
                text_content = "\n".join([r["snippet"] for r in perplexity_res["results"]])
                await self.kb.store_research(
                    company_name, 
                    text_content, 
                    metadata={"source": "perplexity", "scope": scope}
                )
            except Exception as e:
                logger.warning(f"Failed to store research in KB: {e}")

        return {
            "tavily": tavily_res,
            "perplexity": perplexity_res
        }

    async def save_research(
        self, 
        company: str, 
        content: dict, 
        plan_id: str = None, 
        user_id: str = None
    ) -> Dict[str, Any]:
        try:
            supabase = services.get_supabase()
            
            data = {
                "company": company,
                "content": content
            }
            if plan_id:
                data["plan_id"] = plan_id
            if user_id:
                data["user_id"] = user_id
                
            response = await supabase.table("research_data").insert(data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error saving research: {e}")
            return None

    async def aclose(self):
        # AsyncTavilyClient manages its own session per request, so no need to close.
        pass
