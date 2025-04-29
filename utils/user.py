class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String(50), unique=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    phone_number = Column(String(20), unique=True)
    birth_date = Column(String(10))  # ou Column(Date) si mieux typé
    country = Column(String(100))
    country_code = Column(String(10))
    hashed_password = Column(String(255))

    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_restricted = Column(Boolean, default=False)
    photo_url = Column(Text)
    points = Column(Integer, default=0, nullable=False)
    wallet = Column(Integer, default=0, nullable=False)
    referral_code = Column(String(20), unique=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # Relations
    transactions = relationship("Transaction", back_populates="user")
    activities = relationship("Activity", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
