from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Utilisateur
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String(50), unique=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_restricted = Column(Boolean, default=False)
    photo_url = Column(Text)
    points = Column(Integer, default=0, nullable=False)
    wallet = Column(Integer, default=0, nullable=False)
    referral_code = Column(String(20), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Relations
    transactions = relationship("Transaction", back_populates="user")
    activities = relationship("Activity", back_populates="user")


# Transaction liée à un utilisateur
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(10), nullable=False)  # 'credit' ou 'debit'
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


# Activités réalisées par un utilisateur
class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activities")


# Codes de vérification par email
class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True)
    code = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
