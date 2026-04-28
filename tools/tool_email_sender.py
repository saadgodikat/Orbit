import smtplib
from email.message import EmailMessage
from typing import Dict, Any
import os
from tools.base import BaseTool
from core.state_manager import StateManager

class EmailSenderTool(BaseTool):
    """Tool to send emails via SMTP."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_email_sender"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_email_sender\n"
            "DESCRIPTION: Sends an email using SMTP. Assumes SMTP credentials exist in environment variables SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.\n"
            "REQUIRED ARGS:\n"
            "  - to_email (str): The recipient email address\n"
            "  - subject (str): The email subject\n"
            "  - body (str): The content of the email\n"
            "STATE OUTPUT: None"
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        to_email = args.get("to_email")
        subject = args.get("subject")
        body = args.get("body")

        if not to_email or not subject or not body:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_email_sender requires 'to_email', 'subject', and 'body'.")
            return False

        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASSWORD")

        if not smtp_user or not smtp_pass:
            print("\033[38;5;196m[ ERROR ]\033[0m SMTP credentials missing from environment (SMTP_USER, SMTP_PASSWORD).")
            return False

        print(f"\033[38;5;39m[ EMAIL ]\033[0m Sending '{subject}' to {to_email}...")
        
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to_email

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()

            print(f"\033[38;5;114m[ SUCCESS ]\033[0m Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Failed to send email: {e}")
            return False
