from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

class UserLogin(BaseModel):
    email: str
    password: str

class URLCreate(BaseModel):
    original_url: str

class URLOut(BaseModel):
    id: int
    user_id: int
    short_code: str
    click_count: int
    created_at: str

class ClicksOut(BaseModel):
    id: int
    url_id: int
    clicked_at: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

