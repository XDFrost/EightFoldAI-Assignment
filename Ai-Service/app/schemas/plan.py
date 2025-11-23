from typing import Dict, Optional, List
from pydantic import BaseModel, Field

class AccountPlan(BaseModel):
    executive_summary: str = Field(description="Executive summary of the account plan")
    company_overview: str = Field(description="Overview of the company, its business model, and market position")
    strategic_priorities: List[str] = Field(description="List of the company's key strategic priorities")
    opportunities: List[str] = Field(description="List of key opportunities for the account")
    risks: List[str] = Field(description="List of potential risks and mitigation strategies")
    engagement_strategy: str = Field(description="Proposed strategy for engaging with the account")
    next_steps: str = Field(description="Actionable next steps")
