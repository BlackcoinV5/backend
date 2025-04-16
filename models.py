from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, index=True)
    photo_url = Column(Text)
    points = Column(Integer, default=0, nullable=False)
    wallet = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    referral_code = Column(String(20), unique=True)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String(10), nullable=False)  # 'credit' ou 'debit'
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)