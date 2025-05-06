from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    birthdate: str  # Tu peux le typer en `date` si tu veux valider le format ISO
    phone: str = Field(..., min_length=5)
    telegram_username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserVerify(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=8)
