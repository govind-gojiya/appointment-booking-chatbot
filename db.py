from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

def get_current_time():
    return datetime.now(timezone.utc)

engine = create_engine(
    "sqlite:///appointments.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    date = Column(String, index=True)
    time = Column(String, index=True)
    created_at = Column(DateTime, default=get_current_time)

    __table_args__ = (
        UniqueConstraint("date", "time", name="unique_slot"),
    )


class Chat(Base):
    __tablename__ = "chats"

    thread_id = Column(String, primary_key=True)
    user_name = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, default=get_current_time)

Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()