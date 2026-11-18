"""
SQLAlchemy Models for Reel Editor.
"""
import uuid
from datetime import datetime
from typing import Optional

try:
    from sqlalchemy import Column, String, Integer, Float, BigInteger, DateTime, ForeignKey, Text
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.orm import declarative_base, relationship

    Base = declarative_base()

    class Project(Base):
        __tablename__ = "projects"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        name = Column(Text, nullable=False)
        raw_footage_path = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

        jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

    class Job(Base):
        __tablename__ = "jobs"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
        status = Column(String(50), default="pending")
        stage = Column(String(50), default="init")
        progress = Column(Integer, default=0)
        error_message = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        completed_at = Column(DateTime, nullable=True)

        project = relationship("Project", back_populates="jobs")
        edl = relationship("EDLRecord", back_populates="job", uselist=False, cascade="all, delete-orphan")
        render = relationship("RenderMetadata", back_populates="job", uselist=False, cascade="all, delete-orphan")

    class EDLRecord(Base):
        __tablename__ = "edl_records"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
        edl_json = Column(JSONB, nullable=False)
        provider_used = Column(String(100), nullable=True)
        tokens_used = Column(Integer, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)

        job = relationship("Job", back_populates="edl")

    class RenderMetadata(Base):
        __tablename__ = "render_metadata"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
        output_path = Column(Text, nullable=True)
        duration_seconds = Column(Float, nullable=True)
        file_size_bytes = Column(BigInteger, nullable=True)
        benchmark_json = Column(JSONB, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)

        job = relationship("Job", back_populates="render")

except ImportError:
    # If sqlalchemy is not installed in the current environment
    Base = None
    Project = None
    Job = None
    EDLRecord = None
    RenderMetadata = None
