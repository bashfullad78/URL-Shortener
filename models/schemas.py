from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from utils.url_validation import normalize_url


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


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class URLCreate(BaseModel):
    original_url: str

    @field_validator("original_url")
    @classmethod
    def _validate_and_normalize(cls, value: str) -> str:
        """Validate on the way in; the stored URL is always canonical.

        Raises ValueError (InvalidURLError subclasses it) so FastAPI turns
        javascript:/data:/file: and malformed URLs into a 422.
        """
        return normalize_url(value)


class URLOut(BaseModel):
    id: int
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime


class AnalyticsSummary(BaseModel):
    url_id: int
    total_clicks: int
    first_click: Optional[datetime] = None
    last_click: Optional[datetime] = None


class DailyAnalyticsPoint(BaseModel):
    date: date
    clicks: int


class ClicksOut(BaseModel):
    id: int
    url_id: int
    clicked_at: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
