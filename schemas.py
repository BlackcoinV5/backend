# backend/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
import uuid

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    phone_code: str
    phone_number: str
    telegram_username: Optional[str] = None
    email: EmailStr
    country: str
    country_code: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    telegram_username: Optional[str]
    email: str
    is_verified: bool

    class Config:
        orm_mode = True
