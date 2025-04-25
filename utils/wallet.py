# Si le modèle Wallet est séparé, voici un exemple basique :
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)

    user = relationship("User", backref="wallet_instance")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, balance={self.balance})>"
