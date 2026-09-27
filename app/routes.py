from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EmailTemplate, TaskStatus
from app.repository import EmailRepository, EmailTaskRepository, EmailTemplateRepository
from app.schemas import (
    EmailResponse,
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    SendBulkEmailRequest,
    SendEmailResponse,
    SendSingleEmailRequest,
    TaskDetailedResponse,
    TaskResponse,
    TaskStatusResponse,
)
from app.tasks import send_bulk_emails_task, send_single_email_task

router = APIRouter()


@router.post("/templates", response_model=EmailTemplateResponse)
async def create_template(
    template: EmailTemplateCreate,
    session: AsyncSession = Depends(get_db),
):
    """Create a new email template"""
    # Check if template name already exists
    existing = await EmailTemplateRepository.get_by_name(session, template.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template.name}' already exists",
        )

    db_template = await EmailTemplateRepository.create(session, template)
    return db_template


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get template by ID"""
    template = await EmailTemplateRepository.get_by_id(session, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return template


@router.get("/templates", response_model=list[EmailTemplateResponse])
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):
    """List all active templates"""
    templates = await EmailTemplateRepository.list_all(session, skip, limit)
    return templates


@router.get("/templates/name/{name}", response_model=EmailTemplateResponse)
async def get_template_by_name(
    name: str,
    session: AsyncSession = Depends(get_db),
):
    """Get template by name"""
    template = await EmailTemplateRepository.get_by_name(session, name)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{name}' not found",
        )
    return template


@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: UUID,
    template_update: EmailTemplateUpdate,
    session: AsyncSession = Depends(get_db),
):
    """Update template"""
    template = await EmailTemplateRepository.update(
        session, template_id, template_update
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Delete template (soft delete)"""
    success = await EmailTemplateRepository.delete(session, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )


@router.post("/send", response_model=SendEmailResponse)
async def send_single_email(
    request: SendSingleEmailRequest,
    session: AsyncSession = Depends(get_db),
):
    """Send a single email"""

    # Get template if specified
    template: EmailTemplate = None
    html_content = request.html_content
    plain_text_content = request.plain_text_content
    subject = request.subject

    if request.template_name:
        template = await EmailTemplateRepository.get_by_name(
            session, request.template_name
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{request.template_name}' not found",
            )

        # Use template content
        html_content = html_content or template.html_content
        plain_text_content = plain_text_content or template.plain_text_content
        subject = request.subject or template.subject

    # Create email task
    task = await EmailTaskRepository.create(session, task_type="single", total_emails=1)

    # Create email record
    email_data = {
        "task_id": task.id,
        "template_id": template.id if template else None,
        "recipient_email": request.recipient_email,
        "recipient_name": request.recipient_name,
        "subject": subject,
        "html_content": html_content,
        "plain_text_content": plain_text_content,
        "variables": request.variables,
    }
    email = await EmailRepository.create(session, email_data)

    # Send email asynchronously
    celery_task = send_single_email_task.delay(
        email_id=str(email.id),
        recipient_email=email.recipient_email,
        subject=email.subject,
        html_content=email.html_content,
        plain_text_content=email.plain_text_content,
        variables=email.variables,
    )

    # Update task with Celery task ID
    await EmailTaskRepository.update_status(
        session, task.id, TaskStatus.PENDING, celery_task.id
    )

    return SendEmailResponse(
        task_id=task.id,
        message="Email queued for sending",
        status="queued",
    )


@router.post("/send-bulk", response_model=SendEmailResponse)
async def send_bulk_emails(
    request: SendBulkEmailRequest,
    session: AsyncSession = Depends(get_db),
):
    """Send bulk emails"""

    # Get template if specified
    template: EmailTemplate = None
    html_content = request.html_content
    plain_text_content = request.plain_text_content
    subject = request.subject

    if request.template_name:
        template = await EmailTemplateRepository.get_by_name(
            session, request.template_name
        )
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{request.template_name}' not found",
            )

        html_content = html_content or template.html_content
        plain_text_content = plain_text_content or template.plain_text_content
        subject = subject or template.subject

    # Create email task
    task = await EmailTaskRepository.create(
        session, task_type="bulk", total_emails=len(request.recipients)
    )

    # Prepare email data
    emails_data = []
    db_emails = []

    for recipient in request.recipients:
        email_data = {
            "task_id": task.id,
            "template_id": template.id if template else None,
            "recipient_email": recipient.recipient_email,
            "recipient_name": recipient.recipient_name,
            "subject": subject,
            "html_content": html_content,
            "plain_text_content": plain_text_content,
            "variables": recipient.variables,
        }
        db_emails.append(email_data)

    # Create email records in bulk
    emails = await EmailRepository.create_bulk(session, db_emails)

    # Prepare celery task data
    celery_emails_data = [
        {
            "email_id": str(email.id),
            "recipient_email": email.recipient_email,
            "recipient_name": email.recipient_name,
            "subject": email.subject,
            "html_content": email.html_content,
            "plain_text_content": email.plain_text_content,
            "variables": email.variables,
        }
        for email in emails
    ]

    # Send bulk email task
    celery_task = send_bulk_emails_task.delay(
        task_id=str(task.id),
        emails_data=celery_emails_data,
    )

    # Update task with Celery task ID
    await EmailTaskRepository.update_status(
        session, task.id, TaskStatus.PENDING, celery_task.id
    )

    return SendEmailResponse(
        task_id=task.id,
        message=f"{len(request.recipients)} emails queued for sending",
        status="queued",
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailedResponse)
async def get_task_status(
    task_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get task status with detailed email information"""
    task = await EmailTaskRepository.get_by_id(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status_summary(
    task_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get task status summary"""
    task = await EmailTaskRepository.get_by_id(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    completion_percentage = (
        (task.successful_emails + task.failed_emails) / task.total_emails * 100
        if task.total_emails > 0
        else 0
    )

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        total_emails=task.total_emails,
        successful_emails=task.successful_emails,
        failed_emails=task.failed_emails,
        completion_percentage=completion_percentage,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )


@router.get("/tasks", response_model=list[TaskResponse])
async def list_recent_tasks(
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
):
    """List recent tasks"""
    tasks = await EmailTaskRepository.list_recent(session, limit)
    return tasks


@router.get("/tasks/{task_id}/emails", response_model=list[EmailResponse])
async def get_task_emails(
    task_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
):
    """Get emails for a task"""
    # Verify task exists
    task = await EmailTaskRepository.get_by_id(session, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    emails = await EmailRepository.get_by_task_id(session, task_id, skip, limit)
    return emails


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Email service is running"}
