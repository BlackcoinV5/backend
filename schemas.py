from pydantic import BaseModel
from typing import Optional

# --- Schémas Utilisateur ---

class UserBase(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    points: int
    wallet: int

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None


# --- Schémas Transaction ---

class TransactionBase(BaseModel):
    user_id: int
    amount: int
    type: str

    class Config:
        orm_mode = True


class TransactionCreate(BaseModel):
    user_id: int
    amount: int
    type: str
