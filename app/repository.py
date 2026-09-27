from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Email, EmailStatus, EmailTask, EmailTemplate, TaskStatus
from app.schemas import (
    EmailTemplateCreate,
    EmailTemplateUpdate,
)


class EmailTemplateRepository:
    """Repository for EmailTemplate CRUD operations"""

    @staticmethod
    async def create(
        session: AsyncSession, template: EmailTemplateCreate
    ) -> EmailTemplate:
        """Create a new email template"""
        db_template = EmailTemplate(
            name=template.name,
            subject=template.subject,
            html_content=template.html_content,
            plain_text_content=template.plain_text_content,
            variables=template.variables,
        )
        session.add(db_template)
        await session.commit()
        await session.refresh(db_template)
        return db_template

    @staticmethod
    async def get_by_id(
        session: AsyncSession, template_id: UUID
    ) -> EmailTemplate | None:
        """Get template by ID"""
        return await session.get(EmailTemplate, template_id)

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> EmailTemplate | None:
        """Get template by name"""
        stmt = select(EmailTemplate).where(EmailTemplate.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(
        session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[EmailTemplate]:
        """List all active templates"""
        stmt = (
            select(EmailTemplate)
            .where(EmailTemplate.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update(
        session: AsyncSession, template_id: UUID, update_data: EmailTemplateUpdate
    ) -> EmailTemplate | None:
        """Update template"""
        db_template = await session.get(EmailTemplate, template_id)
        if db_template:
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(db_template, key, value)
            await session.commit()
            await session.refresh(db_template)
        return db_template

    @staticmethod
    async def delete(session: AsyncSession, template_id: UUID) -> bool:
        """Soft delete template"""
        db_template = await session.get(EmailTemplate, template_id)
        if db_template:
            db_template.is_active = False
            await session.commit()
            return True
        return False


class EmailTaskRepository:
    """Repository for EmailTask CRUD operations"""

    @staticmethod
    async def create(
        session: AsyncSession, task_type: str, total_emails: int
    ) -> EmailTask:
        """Create a new email task"""
        db_task = EmailTask(task_type=task_type, total_emails=total_emails)
        session.add(db_task)
        await session.commit()
        await session.refresh(db_task)
        return db_task

    @staticmethod
    async def get_by_id(session: AsyncSession, task_id: UUID) -> EmailTask | None:
        """Get task by ID with related emails"""
        stmt = (
            select(EmailTask)
            .where(EmailTask.id == task_id)
            .options(selectinload(EmailTask.emails))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_celery_task_id(
        session: AsyncSession, celery_task_id: str
    ) -> EmailTask | None:
        """Get task by Celery task ID"""
        stmt = select(EmailTask).where(EmailTask.celery_task_id == celery_task_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        session: AsyncSession,
        task_id: UUID,
        status: TaskStatus,
        celery_task_id: str | None = None,
    ) -> EmailTask | None:
        """Update task status"""
        db_task = await session.get(EmailTask, task_id)
        if db_task:
            db_task.status = status
            if celery_task_id:
                db_task.celery_task_id = celery_task_id
            await session.commit()
            await session.refresh(db_task)
        return db_task

    @staticmethod
    async def list_recent(
        session: AsyncSession, limit: int = 50
    ) -> Sequence[EmailTask]:
        """List recent tasks"""
        stmt = select(EmailTask).order_by(desc(EmailTask.created_at)).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()


class EmailRepository:
    """Repository for Email CRUD operations"""

    @staticmethod
    async def create(session: AsyncSession, email_data: dict) -> Email:
        """Create a new email record"""
        db_email = Email(**email_data)
        session.add(db_email)
        await session.commit()
        await session.refresh(db_email)
        return db_email

    @staticmethod
    async def create_bulk(
        session: AsyncSession, emails_data: list[dict]
    ) -> Sequence[Email]:
        """Create multiple email records"""
        db_emails = [Email(**data) for data in emails_data]
        session.add_all(db_emails)
        await session.commit()
        return db_emails

    @staticmethod
    async def get_by_id(session: AsyncSession, email_id: UUID) -> Email | None:
        """Get email by ID"""
        return await session.get(Email, email_id)

    @staticmethod
    async def get_by_task_id(
        session: AsyncSession, task_id: UUID, skip: int = 0, limit: int = 100
    ) -> Sequence[Email]:
        """Get emails by task ID"""
        stmt = select(Email).where(Email.task_id == task_id).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_status(
        session: AsyncSession,
        email_id: UUID,
        status: EmailStatus,
        error_message: str | None = None,
    ) -> Email | None:
        """Update email status"""
        db_email = await session.get(Email, email_id)
        if db_email:
            db_email.status = status
            if error_message:
                db_email.error_message = error_message
            await session.commit()
            await session.refresh(db_email)
        return db_email
