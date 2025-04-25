from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

class TransactionType(enum.Enum):
    credit = "credit"
    debit = "debit"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, type='{self.type.name}', amount={self.amount})>"
