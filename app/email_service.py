import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
from jinja2 import Template, TemplateError

from app.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.timeout = settings.SMTP_TIMEOUT
        self.use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        recipient_email: str,
        recipient_name: str | None = None,
        subject: str = "",
        html_content: str | None = None,
        plain_text_content: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Send a single email

        Args:
            recipient_email: Recipient email address
            recipient_name: Recipient name
            subject: Email subject
            html_content: HTML email body
            plain_text_content: Plain text email body
            variables: Dict of variables for template rendering

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Render templates with variables if provided
            if variables:
                subject = self._render_template(subject, variables)
                if html_content:
                    html_content = self._render_template(html_content, variables)
                if plain_text_content:
                    plain_text_content = self._render_template(
                        plain_text_content, variables
                    )

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"

            if recipient_name:
                message["To"] = f"{recipient_name} <{recipient_email}>"
            else:
                message["To"] = recipient_email

            # Attach plain text first (lower priority)
            if plain_text_content:
                message.attach(MIMEText(plain_text_content, "plain", _charset="utf-8"))

            # Attach HTML (higher priority)
            if html_content:
                message.attach(MIMEText(html_content, "html", _charset="utf-8"))
            elif plain_text_content:
                # If only plain text is provided, ensure it's attached
                pass
            else:
                # Fallback to empty message
                message.attach(MIMEText("", "plain", _charset="utf-8"))

            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                timeout=self.timeout,
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(message)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True, None

        except aiosmtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            logger.error(f"Failed to send email to {recipient_email}: {error_msg}")
            return False, error_msg
        except TemplateError as e:
            error_msg = f"Template rendering error: {e}"
            logger.error(f"Template error for {recipient_email}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"Unexpected error sending to {recipient_email}: {error_msg}")
            return False, error_msg

    @staticmethod
    def _render_template(template_str: str, variables: dict[str, Any]) -> str:
        """Render Jinja2 template with variables"""
        try:
            template = Template(template_str)
            return template.render(**variables)
        except TemplateError as e:
            logger.warning(f"Template rendering failed: {e}. Using original string.")
            return template_str

    @staticmethod
    def get_template_variables(content: str) -> set:
        """Extract variable names from Jinja2 template"""
        try:
            from jinja2 import meta

            ast = meta.find_undeclared_variables(Template(content).module)
            return ast
        except:
            return set()


# Singleton instance
email_service = EmailService()
