from database import Base  # ✅ Correct
from sqlalchemy import Column, Integer, String, Numeric, BigInteger, Text, TIMESTAMP, func

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    profile_picture = Column(Text, nullable=True)
    balance = Column(Numeric, default=0.00)
    level = Column(Integer, default=1)
    ranking = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
