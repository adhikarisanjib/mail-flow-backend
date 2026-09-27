import asyncio
import logging
from datetime import datetime
from typing import Any

from app.celery_app import celery_app
from app.database import get_db_context
from app.email_service import email_service
from app.models import Email, EmailStatus, EmailTask, TaskStatus
from app.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task
def send_single_email_task(
    email_id: str,
    recipient_email: str,
    subject: str,
    html_content: str | None = None,
    plain_text_content: str | None = None,
    variables: dict[str, Any] | None = None,
) -> dict:
    return asyncio.run(
        _send_single_email_task(
            email_id,
            recipient_email,
            subject,
            html_content,
            plain_text_content,
            variables,
        )
    )


async def _send_single_email_task(
    email_id: str,
    recipient_email: str,
    subject: str,
    html_content: str | None = None,
    plain_text_content: str | None = None,
    variables: dict[str, Any] | None = None,
) -> dict:
    """
    Background task to send a single email

    Args:
        email_id: UUID of the email record
        recipient_email: Recipient email address
        subject: Email subject
        html_content: HTML content
        plain_text_content: Plain text content
        variables: Template variables

    Returns:
        Dict with task result
    """
    try:
        # Send email via SMTP
        success, error_msg = await email_service.send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text_content,
            variables=variables,
        )

        # Update email record
        async with get_db_context() as session:
            email = await session.get(Email, email_id)
            if email:
                email.attempts += 1
                if success:
                    email.status = EmailStatus.SENT
                    email.sent_at = datetime.utcnow()
                else:
                    email.status = EmailStatus.FAILED
                    email.error_message = error_msg

                    # Retry if max attempts not reached
                    if email.attempts < email.max_attempts:
                        await session.commit()
                        raise Exception(
                            f"Email failed, retrying. Attempt {email.attempts}"
                        )

                await session.commit()
                logger.info(f"Email {email_id} status updated: {email.status}")

        if not success:
            logger.error(f"Failed to send email {email_id}: {error_msg}")
            return {
                "status": "failed",
                "email_id": email_id,
                "error": error_msg,
            }

        return {
            "status": "success",
            "email_id": email_id,
        }

    except Exception as exc:
        logger.error(f"Task error for email {email_id}: {str(exc)}")


@celery_app.task
def send_bulk_emails_task(task_id: str, emails_data: list[dict[str, Any]]) -> dict:
    return asyncio.run(_send_bulk_emails_task(task_id, emails_data))


async def _send_bulk_emails_task(
    task_id: str,
    emails_data: list[dict[str, Any]],
) -> dict:
    """
    Background task to send bulk emails

    Args:
        task_id: UUID of the email task
        emails_data: List of email data dicts

    Returns:
        Dict with task result
    """
    try:
        # Update task status to processing
        async with get_db_context() as session:
            task = await session.get(EmailTask, task_id)
            if task:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.utcnow()
                await session.commit()

        # Process emails in batches
        batch_size = settings.BATCH_SIZE
        total_emails = len(emails_data)
        successful = 0
        failed = 0

        for i in range(0, total_emails, batch_size):
            batch = emails_data[i : i + batch_size]

            # Send emails in batch
            for email_data in batch:
                email_id = email_data["email_id"]

                try:
                    # Send email
                    success, error_msg = await email_service.send_email(
                        recipient_email=email_data["recipient_email"],
                        recipient_name=email_data.get("recipient_name"),
                        subject=email_data["subject"],
                        html_content=email_data.get("html_content"),
                        plain_text_content=email_data.get("plain_text_content"),
                        variables=email_data.get("variables"),
                    )

                    # Update email record
                    async with get_db_context() as session:
                        email = await session.get(Email, email_id)
                        if email:
                            email.attempts += 1
                            if success:
                                email.status = EmailStatus.SENT
                                email.sent_at = datetime.utcnow()
                                successful += 1
                            else:
                                email.status = EmailStatus.FAILED
                                email.error_message = error_msg
                                failed += 1
                            await session.commit()

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    failed += 1

                    # Update email status
                    async with get_db_context() as session:
                        email = await session.get(Email, email_id)
                        if email:
                            email.status = EmailStatus.FAILED
                            email.error_message = str(e)
                            email.attempts += 1
                            await session.commit()

        # Update task completion
        async with get_db_context() as session:
            task = await session.get(EmailTask, task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.successful_emails = successful
                task.failed_emails = failed
                task.completed_at = datetime.utcnow()
                await session.commit()

        logger.info(
            f"Bulk email task {task_id} completed. "
            f"Successful: {successful}, Failed: {failed}"
        )

        return {
            "status": "completed",
            "task_id": task_id,
            "successful": successful,
            "failed": failed,
        }

    except Exception as exc:
        logger.error(f"Bulk email task {task_id} failed: {str(exc)}")

        # Update task as failed
        async with get_db_context() as session:
            task = await session.get(EmailTask, task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc)
                task.completed_at = datetime.utcnow()
                await session.commit()

        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(exc),
        }
