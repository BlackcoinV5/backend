# backend/models.py
from sqlalchemy import Column, String, Date, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean
import uuid
from database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    phone_code = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    telegram_username = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    country = Column(String, nullable=False)
    country_code = Column(String(2), nullable=False)
    password_hash = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verification_code = Column(String, nullable=True)  # 👈 Ajouté
