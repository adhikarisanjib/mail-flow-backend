import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=True)
    plain_text_content = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True, default={})  # List of expected variables
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    emails = relationship("Email", back_populates="template")

    def __repr__(self):
        return f"<EmailTemplate {self.name}>"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EmailTask(Base):
    __tablename__ = "email_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False)  # "single" or "bulk"
    status = Column(
        SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True
    )
    total_emails = Column(Integer, default=1)
    successful_emails = Column(Integer, default=0)
    failed_emails = Column(Integer, default=0)
    celery_task_id = Column(String(255), nullable=True, index=True, unique=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional task info
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    emails = relationship("Email", back_populates="task")

    def __repr__(self):
        return f"<EmailTask {self.id} - {self.status}>"


class EmailStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("email_tasks.id"), nullable=False, index=True
    )
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("email_templates.id"), nullable=True
    )
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    html_content = Column(Text, nullable=True)
    plain_text_content = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True)  # Variables used for this email
    status = Column(
        SQLEnum(EmailStatus), nullable=False, default=EmailStatus.QUEUED, index=True
    )
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    task = relationship("EmailTask", back_populates="emails")
    template = relationship("EmailTemplate", back_populates="emails")

    def __repr__(self):
        return f"<Email {self.recipient_email} - {self.status}>"
