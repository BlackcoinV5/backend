# backend/models.py

import uuid
from sqlalchemy import Column, String, Date, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)

    phone_code = Column(String, nullable=False)  # Ex: "+33"
    phone_number = Column(String, nullable=False)  # Ex: "612345678"

    telegram_username = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)

    country = Column(String, nullable=False)  # Ex: "France"
    country_code = Column(String(2), nullable=False)  # Ex: "FR"

    password_hash = Column(String, nullable=False)  # Hash du mot de passe
    is_verified = Column(Boolean, default=False)

    verification_code = Column(String, nullable=True)  # Code envoyé par email
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<User {self.first_name} {self.last_name} ({self.email})>"
