from pydantic import BaseModel, ConfigDict
from typing import Optional


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class UserSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, alias_generator=_to_camel)
    id: str
    username: str
    role: str
    email: str
    allowed_agent_ids: Optional[list[str]] = None


class UserCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    username: str
    email: str
    password: Optional[str] = None
    role: str = "REGULAR_USER"


class UserUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)
    role: Optional[str] = None
    allowed_agent_ids: Optional[list[str]] = None
    username: Optional[str] = None
    email: Optional[str] = None
