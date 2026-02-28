from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from src.database.config import Base

from sqlalchemy.orm import relationship

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Index,
)


class Transcription(Base):
    __tablename__ = "transcriptions"

    file_id = Column(String(255), primary_key=True, nullable=False)

    transcription_text = Column(Text, nullable=True)

    language = Column(String(50), nullable=True)

    gpt_response = Column(Text, nullable=True)

    iscorrect = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Transcription(file_id='{self.file_id}', language='{self.language}')>"


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(255), primary_key=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usage_records = relationship("UserUsage", back_populates="user", cascade="all, delete-orphan")

class UserUsage(Base):
    __tablename__ = "user_usage"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="usage_records")

    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uix_user_day"),

        Index("idx_user_day", "user_id", "day"),
    )

