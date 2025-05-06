from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base  # ← Correction ici (tu avais écrit `Bas`)

# -------------------- UTILISATEUR --------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    telegram_username = Column(String)
    avatar_url = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(String)
    phone = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=False)  # activé après vérif e-mail
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="user", uselist=False)
    level = relationship("Level", back_populates="user", uselist=False)
    ranking = relationship("Ranking", back_populates="user", uselist=False)

# -------------------- VÉRIFICATION E-MAIL --------------------

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

# -------------------- WALLET --------------------

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)
    mined = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)

    user = relationship("User", back_populates="wallet")

# -------------------- NIVEAU --------------------

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    level = Column(Integer, default=1)
    xp = Column(Float, default=0.0)

    user = relationship("User", back_populates="level")

# -------------------- ACTIONS --------------------

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class MyAction(Base):
    __tablename__ = "my_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_id = Column(Integer, ForeignKey("actions.id"))
    status = Column(String, default="pending")  # pending | validated | rejected
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- TÂCHES --------------------

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    is_validated = Column(Boolean, default=False)
    validated_at = Column(DateTime, nullable=True)

# -------------------- AMIS --------------------

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- CLASSEMENT --------------------

class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    points = Column(Float, default=0.0)
    position = Column(Integer)

    user = relationship("User", back_populates="ranking")
