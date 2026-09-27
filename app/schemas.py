from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class EmailTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    html_content: str | None = None
    plain_text_content: str | None = None
    variables: list[str] | None = None  # List of variable names used in template


class EmailTemplateUpdate(BaseModel):
    subject: str | None = None
    html_content: str | None = None
    plain_text_content: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class EmailTemplateResponse(BaseModel):
    id: UUID
    name: str
    subject: str
    html_content: str | None
    plain_text_content: str | None
    variables: list[str] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SendSingleEmailRequest(BaseModel):
    recipient_email: EmailStr
    recipient_name: str | None = None
    subject: str
    template_name: str | None = None
    html_content: str | None = None
    plain_text_content: str | None = None
    variables: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_request(self):
        if not self.subject:
            raise ValueError("subject is required")

        content_count = sum(
            bool(x)
            for x in (
                self.template_name,
                self.html_content,
                self.plain_text_content,
            )
        )

        if content_count == 0:
            raise ValueError(
                "Either template_name or html_content/plain_text_content "
                "must be provided"
            )

        if content_count > 1:
            raise ValueError(
                "Provide only one of template_name, html_content, "
                "or plain_text_content"
            )

        return self


class BulkEmailItem(BaseModel):
    recipient_email: EmailStr
    recipient_name: str | None = None
    variables: dict[str, Any] | None = None


class SendBulkEmailRequest(BaseModel):
    template_name: str | None = None
    subject: str | None = None
    html_content: str | None = None
    plain_text_content: str | None = None
    recipients: list[BulkEmailItem] = Field(..., min_items=1)

    @model_validator(mode="after")
    def validate_request(self):
        if not self.subject:
            raise ValueError("subject is required")

        content_count = sum(
            bool(x)
            for x in (
                self.template_name,
                self.html_content,
                self.plain_text_content,
            )
        )

        if content_count == 0:
            raise ValueError(
                "Either template_name or html_content/plain_text_content "
                "must be provided"
            )

        if content_count > 1:
            raise ValueError(
                "Provide only one of template_name, html_content, "
                "or plain_text_content"
            )

        return self


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EmailStatusEnum(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailResponse(BaseModel):
    id: UUID
    recipient_email: str
    recipient_name: str | None
    subject: str
    status: EmailStatusEnum
    attempts: int
    sent_at: datetime | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: UUID
    task_type: str
    status: TaskStatusEnum
    total_emails: int
    successful_emails: int
    failed_emails: int
    celery_task_id: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class TaskDetailedResponse(TaskResponse):
    emails: list[EmailResponse] = []


class SendEmailResponse(BaseModel):
    task_id: UUID
    message: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: UUID
    status: TaskStatusEnum
    total_emails: int
    successful_emails: int
    failed_emails: int
    completion_percentage: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
