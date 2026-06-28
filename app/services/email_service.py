import os
from typing import Optional
from datetime import datetime
import aiosmtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

class EmailService:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = os.environ.get("SMTP_USERNAME")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@nonprofit.org")
        self.from_name = os.environ.get("FROM_NAME", "Nonprofit Organization")
        # Outreach signature and reply-to per branding rules
        self.reply_to = os.environ.get("REPLY_TO_EMAIL", "shinelikeacrime@gmail.com")
        self.signature_block = (
            "\n—\n"
            "Michael Yessian\n"
            "Community Outreach, Lawton OK\n"
            "Reply-to: shinelikeacrime@gmail.com\n"
            "Text only: 405-204-1427 (this number is for text communication only)\n"
        )
    
    async def send_receipt_email(
        self,
        to_email: str,
        donor_name: str,
        receipt_number: str,
        pdf_path: str,
        amount: float
    ) -> bool:
        """Send receipt email with PDF attachment"""
        
        if not self.smtp_password or not self.smtp_username:
            print("Email service not configured: Missing SMTP credentials")
            return False

        try:
            message = MIMEMultipart()
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = f"Your Donation Receipt #{receipt_number}"
            message["Reply-To"] = self.reply_to
            
            # Email body
            body = f"""
Dear {donor_name},

Thank you for your generous donation of ${amount:.2f}.

Attached is your official receipt for tax purposes. Please keep this for your records.

Receipt Number: {receipt_number}
Date: {datetime.now().strftime("%B %d, %Y")}

If you have any questions, please don't hesitate to contact us.

Warm regards,
{self.from_name}
{self.signature_block}
"""
            
            message.attach(MIMEText(body, "plain"))
            
            # Attach PDF if it exists
            if Path(pdf_path).exists():
                with open(pdf_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name="receipt.pdf")
                    part["Content-Disposition"] = f'attachment; filename="receipt_{receipt_number}.pdf"'
                    message.attach(part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_simple_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """Send simple text email"""
        
        try:
            message = EmailMessage()
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            message["Reply-To"] = self.reply_to
            # Append mandatory signature if not already present
            body_with_sig = body if self.signature_block.strip() in body else f"{body}\n{self.signature_block}"
            message.set_content(body_with_sig)
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False