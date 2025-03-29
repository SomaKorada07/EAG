import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

class EmailTool:
    def __init__(self):
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_APP_PASSWORD")
        self.smtp_server = "smtp.gmail.com"  # Using Gmail SMTP as an example
        self.smtp_port = 587

    def send_email(self, recipient: str, subject: str, content: str) -> None:
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.smtp_email
            message["To"] = recipient
            message["Subject"] = subject

            # Add body
            message.attach(MIMEText(content, "plain"))

            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(message)
                
            logger.info(f"Email sent successfully to {recipient}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            raise Exception(f"Failed to send email: {str(e)}") 