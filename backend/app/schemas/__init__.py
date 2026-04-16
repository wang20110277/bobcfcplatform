from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.user import UserSchema, UserUpdate, _to_camel as _tc  # noqa: F401


_to_camel = _tc


class SkillSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    id: str
    name: str
    description: str
    type: str
    status: str


class SkillUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class AgentSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    id: str
    name: str
    description: str
    status: str
    skill_ids: list[str] = []
    recommended_model: Optional[str] = None


class AgentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    skill_ids: Optional[list[str]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    recommended_model: Optional[str] = None


class MessageSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    role: str
    content: str
    timestamp: str


class ConversationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    id: str
    user_id: str
    agent_id: Optional[str] = None
    messages: list[MessageSchema] = []
    title: str
    model_id: Optional[str] = None


class ConversationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    agent_id: Optional[str] = None
    title: Optional[str] = None
    model_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    model_id: Optional[str] = None


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    message: str
    conversation_id: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    content: str
    conversation: ConversationSchema


class ArtifactSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    id: str
    session_id: str
    name: str
    type: str
    status: str
    created_at: str
    storage_path: Optional[str] = None


class ArtifactGenerate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    type: str
    session_id: str
    name: Optional[str] = None
