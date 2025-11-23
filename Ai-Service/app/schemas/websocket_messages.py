from typing import Optional, Dict, Any, Literal, Union, List
from pydantic import BaseModel

class UserMessagePayload(BaseModel):
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    text: str
    selected_text: Optional[str] = None
    source_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UserMessage(BaseModel):
    type: Literal["user_message"] = "user_message"
    payload: UserMessagePayload

class StatusUpdatePayload(BaseModel):
    stage: str
    message: str
    progress: Optional[float] = None

class StatusUpdate(BaseModel):
    type: Literal["status_update"] = "status_update"
    payload: StatusUpdatePayload

class AssistantChunkPayload(BaseModel):
    message_id: str
    chunk: str

class AssistantChunk(BaseModel):
    type: Literal["assistant_chunk"] = "assistant_chunk"
    payload: AssistantChunkPayload

class PlanUpdatePayload(BaseModel):
    plan_id: str
    section: str
    content: Union[str, List[str]]

class PlanUpdate(BaseModel):
    type: Literal["plan_update"] = "plan_update"
    payload: PlanUpdatePayload

class ErrorPayload(BaseModel):
    code: str
    message: str

class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    payload: ErrorPayload

class MessageUpdatePayload(BaseModel):
    message_id: str
    content: str

class MessageUpdate(BaseModel):
    type: Literal["message_update"] = "message_update"
    payload: MessageUpdatePayload
