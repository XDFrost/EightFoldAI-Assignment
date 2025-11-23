from pydantic import BaseModel, Field
from typing import Literal, Optional

class Entities(BaseModel):
    company: Optional[str] = Field(None, description="The company name mentioned in the message")
    region: Optional[str] = Field(None, description="The region mentioned, if any")
    section: Optional[str] = Field(None, description="The section to edit, if any")

class IntentAnalysis(BaseModel):
    intent: Literal["research_company", "generate_plan", "edit_section", "chat", "answer_clarification"] = Field(
        description="The user's intent."
    )
    entities: Entities = Field(
        default_factory=Entities,
        description="Extracted entities from the message."
    )
