from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    password: str
    avatar_url: Optional[str] = None