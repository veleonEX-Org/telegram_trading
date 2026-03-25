import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_notification_email(subject: str, body: str):
    """
    Send a simple notification email using SMTP credentials from configs.
    """
    if not settings.notification_email or not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP email notifications are not fully configured. Skipping.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_user
        msg['To'] = settings.notification_email
        msg['Subject'] = f"[VELEONEX Alert] {subject}"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            
        logger.info(f"Notification email sent: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False
