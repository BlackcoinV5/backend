from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# === Schémas Utilisateur ===

class UserBase(BaseModel):
    id: int = Field(..., examples=[123456789])
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=255)
    points: int = Field(0, ge=0)
    wallet: int = Field(0, ge=0)
    referral_code: Optional[str] = Field(None, max_length=20)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    id: int = Field(..., examples=[123456789])
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=255)
    referral_code: Optional[str] = Field(None, max_length=20)

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    birth_date: Optional[str] = Field(None, max_length=10)  # format YYYY-MM-DD
    password: Optional[str] = Field(None, min_length=6)

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    created_at: datetime
    last_login: Optional[datetime]


# === Schémas Transactions ===

class TransactionBase(BaseModel):
    user_id: int
    amount: int = Field(..., gt=0)
    type: str = Field(..., pattern="^(credit|debit)$")
    description: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
