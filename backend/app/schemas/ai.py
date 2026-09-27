from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "en"  # en, hi, hinglish


class ToolCallExecution(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = True


class AIChatResponse(BaseModel):
    conversation_id: str
    reply: str
    response: Optional[str] = None
    intent: Optional[str] = None
    tool_calls: Optional[List[ToolCallExecution]] = None
    is_emergency: bool = False
    escalation_triggered: bool = False
    suggested_actions: Optional[List[str]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.response is None:
            self.response = self.reply


class AIMessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender: str
    content: str
    intent: Optional[str] = None
    tool_calls: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIConversationResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    channel: str
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[AIMessageResponse]] = None

    model_config = {"from_attributes": True}

