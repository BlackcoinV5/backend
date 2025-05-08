from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# -------------------- UTILISATEUR --------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=True)
    telegram_username = Column(String, unique=True, nullable=True)
    avatar_url = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    level = relationship("Level", back_populates="user", uselist=False, cascade="all, delete-orphan")
    ranking = relationship("Ranking", back_populates="user", uselist=False, cascade="all, delete-orphan")
    actions = relationship("MyAction", backref="user", cascade="all, delete-orphan")
    tasks = relationship("Task", backref="user", cascade="all, delete-orphan")
    friendships = relationship("Friendship", foreign_keys="[Friendship.user_id]", backref="user", cascade="all, delete-orphan")
    friends = relationship("Friendship", foreign_keys="[Friendship.friend_id]", backref="friend", cascade="all, delete-orphan")


# -------------------- VÉRIFICATION E-MAIL --------------------

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


# -------------------- WALLET --------------------

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)
    mined = Column(Float, default=0.0)
    spent = Column(Float, default=0.0)

    user = relationship("User", back_populates="wallet")


# -------------------- NIVEAU --------------------

class Level(Base):
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Float, default=0.0)

    user = relationship("User", back_populates="level")


# -------------------- ACTIONS --------------------

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MyAction(Base):
    __tablename__ = "my_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    status = Column(String, default="pending")  # pending | validated | rejected
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------- TÂCHES --------------------

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    is_validated = Column(Boolean, default=False)
    validated_at = Column(DateTime, nullable=True)


# -------------------- AMIS --------------------

class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------- CLASSEMENT --------------------

class Ranking(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Float, default=0.0)
    position = Column(Integer, nullable=True)

    user = relationship("User", back_populates="ranking")
