from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Boolean, Float, ForeignKey, Enum as SqlEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from database import Base


# -------------------------
# Enum pour le type de transaction
# -------------------------
class TransactionType(Enum):
    CREDIT = "credit"
    DEBIT = "debit"


# -------------------------
# Table Utilisateurs
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String(50), unique=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, index=True)  # utilisé pour l'auth
    email = Column(String(100), unique=True, index=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_restricted = Column(Boolean, default=False)
    photo_url = Column(Text)
    points = Column(Integer, default=0, nullable=False)
    wallet = Column(Integer, default=0, nullable=False)
    referral_code = Column(String(20), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relations
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


# -------------------------
# Table Transactions
# -------------------------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(SqlEnum(TransactionType), nullable=False)  # credit ou debit
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type='{self.type.name}', amount={self.amount})>"


# -------------------------
# Table Activités
# -------------------------
class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="activities")

    def __repr__(self):
        return f"<Activity(id={self.id}, user_id={self.user_id}, date={self.date})>"


# -------------------------
# Table Codes de vérification Email
# -------------------------
class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True)
    code = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))

    def __repr__(self):
        return f"<EmailVerificationCode(email='{self.email}', code='{self.code}')>"


# -------------------------
# Fonction utilitaire : requête par username Telegram
# -------------------------
def select_user_by_telegram_username(username: str):
    return select(User).where(User.telegram_username == username)
