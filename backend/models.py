from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    skills = Column(JSON)
    location = Column(String)
    availability = Column(String)
    contact = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Need(Base):
    __tablename__ = "needs"

    id = Column(Integer, primary_key=True, index=True)
    source_text = Column(Text)
    category = Column(String)
    location = Column(String)
    urgency_score = Column(Integer)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    need_id = Column(Integer, ForeignKey("needs.id"))
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"))
    match_score = Column(Integer)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text)
    uploaded_by = Column(String)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
