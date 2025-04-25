from sqlalchemy import Column, Integer, String
from backend.database import Base

class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    def __repr__(self):
        return f"<Status(id={self.id}, name='{self.name}')>"
