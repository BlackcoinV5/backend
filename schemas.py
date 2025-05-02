from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional
import uuid


# ✅ Schéma pour la création d’un utilisateur
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


# ✅ Schéma pour la réponse utilisateur après création ou login
class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    telegram_username: Optional[str] = None
    is_verified: bool

    class Config:
        orm_mode = True


# ✅ (Optionnel) Schéma utilisé pour afficher les données complètes du profil
class UserFullResponse(UserResponse):
    wallet: Optional[float] = 0.0
    points: Optional[int] = 0
    level: Optional[int] = 1
