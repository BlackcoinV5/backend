from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    id: int = Field(..., examples=[123456789])
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = None
    points: int = Field(0, ge=0)
    wallet: int = Field(0, ge=0)
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    referral_code: Optional[str] = Field(None, max_length=20)

class TransactionBase(BaseModel):
    user_id: int
    amount: int = Field(..., gt=0)
    type: str = Field(..., pattern="^(credit|debit)$")
    description: Optional[str] = Field(None, max_length=255)
    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    created_at: datetime
    last_login: Optional[datetime]