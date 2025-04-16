from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# --- Schémas Utilisateur de base ---
class UserBase(BaseModel):
    id: int = Field(..., examples=[123456789])
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = None
    points: int = Field(0, ge=0)
    wallet: int = Field(0, ge=0)

    model_config = ConfigDict(from_attributes=True)


# --- Schéma de création d'un nouvel utilisateur ---
class UserCreate(UserBase):
    referral_code: Optional[str] = Field(None, max_length=20)


# --- Schéma de mise à jour des données utilisateur ---
class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Schéma de réponse utilisateur (lecture depuis la base) ---
class UserResponse(UserBase):
    created_at: datetime
    last_login: Optional[datetime]


# --- Schémas pour les transactions ---
class TransactionBase(BaseModel):
    user_id: int
    amount: int = Field(..., gt=0)
    type: str = Field(..., pattern="^(credit|debit)$")
    description: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


# --- Schéma de réponse pour une transaction (avec ID et timestamps) ---
class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime