from app.states.global_state import services
from app.utils.logger import logger
from typing import Dict, Any

class PlanService:
    def __init__(self) -> None:
        pass

    @property
    def client(self):
        return services.get_supabase()

    async def create_plan(
        self, 
        plan_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            response = await self.client.table("account_plans")\
                                .insert(plan_data)\
                                .execute()
            
            if response.data:
                return response.data[0]
            return plan_data        # Fallback
        
        except Exception as e:
            logger.error(f"Error creating plan in Supabase: {e}")
            return None

    async def get_plan(
        self, 
        plan_id: str
    ) -> Dict[str, Any]:
        try:
            response = await self.client.table("account_plans")\
                        .select("*")\
                        .eq("id", plan_id)\
                        .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching plan: {e}")
            return None

    async def get_latest_plan_by_company(
        self, 
        company: str, 
        user_id: str = None
    ) -> Dict[str, Any]:
        try:
            query = self.client.table("account_plans")\
                .select("*")\
                .eq("company", company)
            
            if user_id:
                query = query.eq("user_id", user_id)
                
            response = await query.order("created_at", desc=True)\
                        .limit(1)\
                        .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching plan: {e}")
            return None

    async def update_section(
        self, 
        plan_id: str, 
        section: str, 
        content: str
    ) -> Dict[str, Any]:
        try:
            # fetch, update dict, save back.
            current_plan = await self.client.table("account_plans")\
                            .select("sections")\
                            .eq("id", plan_id)\
                            .single().execute()
            if not current_plan.data:
                return None
            
            sections = current_plan.data.get("sections", {})
            sections[section] = content
            
            response = await self.client.table("account_plans")\
                        .update({"sections": sections})\
                        .eq("id", plan_id)\
                        .execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating section: {e}")
            return None
