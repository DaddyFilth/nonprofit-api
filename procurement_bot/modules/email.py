"""
Email and outreach engine for the procurement bot.

Handles email automation via SMTP, Gmail API, or SendGrid, monitors
inbox for replies, and logs responses in the database.
"""

import asyncio
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from procurement_bot.config import settings


class EmailProvider:
    """Base class for email providers."""
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email."""
        raise NotImplementedError
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """Check for email replies since a given time."""
        raise NotImplementedError


class SMTPEmailProvider(EmailProvider):
    """Email provider using SMTP."""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = to
            
            # Attach plain text version
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML version if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"✓ Email sent to {to}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send email to {to}: {e}")
            return False
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """SMTP cannot check for replies without IMAP."""
        print("Warning: SMTP provider cannot check for replies. Use Gmail API or SendGrid for this feature.")
        return []


class SendGridEmailProvider(EmailProvider):
    """Email provider using SendGrid API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email via SendGrid API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to}],
                        "subject": subject
                    }
                ],
                "from": {"email": settings.bot_email},
                "content": [
                    {"type": "text/plain", "value": body}
                ]
            }
            
            if html_body:
                data["content"].append({"type": "text/html", "value": html_body})
            
            response = requests.post(
                f"{self.base_url}/mail/send",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 202]:
                print(f"✓ Email sent to {to}")
                return True
            else:
                print(f"✗ Failed to send email to {to}: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to send email to {to}: {e}")
            return False
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """Check for email replies using SendGrid API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
            }
            
            # Query messages received since the given time
            params = {
                "limit": 50,
                "query": f"last_event_time>={int(since.timestamp())}"
            }
            
            response = requests.get(
                f"{self.base_url}/messages",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                replies = []
                
                for message in data.get("messages", []):
                    if message.get("direction") == "inbound":
                        replies.append({
                            "from": message.get("from", ""),
                            "subject": message.get("subject", ""),
                            "body": message.get("content", ""),
                            "timestamp": datetime.fromtimestamp(
                                message.get("last_event_time", 0),
                                timezone.utc
                            ),
                        })
                
                return replies
            else:
                print(f"Failed to check replies: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error checking replies: {e}")
            return []


class GmailAPIProvider(EmailProvider):
    """Email provider using Gmail API (simplified implementation)."""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
    
    async def _get_access_token(self) -> str:
        """Get access token using refresh token."""
        # This is a simplified implementation. In production, use proper OAuth2 flow
        # and token caching. For now, we'll return a placeholder.
        return "placeholder_access_token"
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email via Gmail API."""
        try:
            import base64
            
            access_token = await self._get_access_token()
            
            # Create email message
            message = MIMEMultipart('alternative')
            message['To'] = to
            message['From'] = settings.bot_email
            message['Subject'] = subject
            
            message.attach(MIMEText(body, 'plain'))
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"raw": raw}
            
            response = requests.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✓ Email sent to {to}")
                return True
            else:
                print(f"✗ Failed to send email to {to}: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to send email to {to}: {e}")
            return False
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """Check for email replies using Gmail API."""
        try:
            access_token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
            }
            
            # Search for messages since the given time
            query = f"after:{int(since.timestamp())}"
            response = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                replies = []
                
                for message_ref in data.get("messages", []):
                    # Get message details
                    msg_response = requests.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_ref['id']}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if msg_response.status_code == 200:
                        msg_data = msg_response.json()
                        
                        # Extract headers
                        headers_dict = {}
                        for header in msg_data.get("payload", {}).get("headers", []):
                            headers_dict[header["name"]] = header["value"]
                        
                        replies.append({
                            "from": headers_dict.get("From", ""),
                            "subject": headers_dict.get("Subject", ""),
                            "body": "",  # Would need to parse payload for actual body
                            "timestamp": datetime.fromtimestamp(
                                int(msg_data.get("internalDate", 0)) / 1000,
                                timezone.utc
                            ),
                        })
                
                return replies
            else:
                print(f"Failed to check replies: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error checking replies: {e}")
            return []


class EmailTemplate:
    """Email template generator for donation requests with strict system prompt requirements."""
    
    @staticmethod
    def get_materials_list() -> str:
        """Get the dynamic materials list for restoration projects with usage explanations."""
        return """• Commercial-grade driveway sealants - to restore safe, accessible driveways for elderly residents
• Treated lumber and hardware - for safe deck and ramp repairs to prevent falls and improve accessibility
• Vinyl siding cleaning solutions - to restore home exteriors and community pride
• Heavy-duty applicators - essential equipment for professional-quality repairs
• Exterior paint and primers - to protect and beautify homes for vulnerable families
• Weatherproofing materials - to keep homes safe and dry during Oklahoma weather
• Concrete repair products - to fix hazardous walkways and entry points
• Masonry sealants - to preserve structural integrity of older homes"""
    
    @staticmethod
    def generate_donation_request(
        supplier_name: str,
        contact_person: Optional[str] = None,
        material_type: str = "building materials",
        organization_name: str = None,
        project_description: str = None
    ) -> tuple[str, str]:
        """Generate a personalized donation request email with strict 4-pillar structure."""
        
        org_name = organization_name or settings.organization_name
        greeting = f"Dear {contact_person}" if contact_person else f"Dear {supplier_name} Team"
        
        materials_list = EmailTemplate.get_materials_list()
        
        plain_text = f"""
{greeting},

I hope this email finds you well. I am reaching out on behalf of {settings.organization_operating_names}, a {settings.organization_mission} based in {settings.organization_location}.

**WHO WE ARE**
{settings.organization_operating_names} is a community-driven initiative dedicated to providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost to them. We believe that everyone deserves to live in a safe, well-maintained home, regardless of their financial situation.

**MATERIALS NEEDED FOR CURRENT & FUTURE PROJECTS**
We are currently seeking donations of the following materials to fulfill our charitable projects:

{materials_list}

Your expertise in {material_type} would be particularly valuable for our current projects.

These materials directly help vulnerable neighbors stay safe and proud of their homes. Every donation enables us to repair hazardous conditions, improve accessibility for elderly residents, and restore dignity to families who have fallen on hard times.

**COMMUNITY IMPACT**
Your material donation will:
- Keep elderly residents safe in their homes by fixing fall hazards and structural issues
- Allow low-income families to remain in their homes instead of facing displacement
- Restore community pride neighborhood by neighborhood
- Provide immediate, tangible help to neighbors who need it most

**TAX DEDUCTION BENEFITS**
Donating excess inventory or building materials to our organization serves as a strategic tax write-off for your business. Under general IRS Section 170 guidelines for corporate inventory donations, your contribution may qualify for significant tax advantages.

Upon receipt of donated materials, we will provide all necessary documentation and tax receipts for your corporate giving records, ensuring a smooth and compliant process for your accounting department.

**NEXT STEPS**
If you're interested in supporting our mission to help elderly and low-income families through material donation, please reply to this email. We are happy to provide detailed information about our organization, specific project needs, and coordinate material pickup or delivery logistics.

Thank you for considering this opportunity to make a meaningful difference in the lives of vulnerable {settings.organization_location} residents.

Best regards,

Michael Yessian
{settings.organization_operating_names}
Reply-to: {settings.reply_to_email}
{settings.contact_phone} (Text communication only)
"""
        
        html_text = f"""
<html>
<body>
<h2>{greeting},</h2>

<p>I hope this email finds you well. I am reaching out on behalf of <strong>{settings.organization_operating_names}</strong>, a {settings.organization_mission} based in {settings.organization_location}.</p>

<h3>WHO WE ARE</h3>
<p><strong>{settings.organization_operating_names}</strong> is a community-driven initiative dedicated to providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost to them. We believe that everyone deserves to live in a safe, well-maintained home, regardless of their financial situation.</p>

<h3>MATERIALS NEEDED FOR CURRENT & FUTURE PROJECTS</h3>
<p>We are currently seeking donations of the following materials to fulfill our charitable projects:</p>
<ul>
{materials_list.replace('• ', '<li>').replace('\n• ', '</li>\n<li>').replace('\n', '</li>\n')}
</ul>
<p>Your expertise in {material_type} would be particularly valuable for our current projects.</p>
<p>These materials directly help vulnerable neighbors stay safe and proud of their homes. Every donation enables us to repair hazardous conditions, improve accessibility for elderly residents, and restore dignity to families who have fallen on hard times.</p>

<h3>COMMUNITY IMPACT</h3>
<p>Your material donation will:</p>
<ul>
<li>Keep elderly residents safe in their homes by fixing fall hazards and structural issues</li>
<li>Allow low-income families to remain in their homes instead of facing displacement</li>
<li>Restore community pride neighborhood by neighborhood</li>
<li>Provide immediate, tangible help to neighbors who need it most</li>
</ul>

<h3>TAX DEDUCTION BENEFITS</h3>
<p>Donating excess inventory or building materials to our organization serves as a strategic tax write-off for your business. Under general IRS Section 170 guidelines for corporate inventory donations, your contribution may qualify for significant tax advantages.</p>
<p>Upon receipt of donated materials, we will provide all necessary documentation and tax receipts for your corporate giving records, ensuring a smooth and compliant process for your accounting department.</p>

<h3>NEXT STEPS</h3>
<p>If you're interested in supporting our mission to help elderly and low-income families through material donation, please reply to this email. We are happy to provide detailed information about our organization, specific project needs, and coordinate material pickup or delivery logistics.</p>

<p>Thank you for considering this opportunity to make a meaningful difference in the lives of vulnerable {settings.organization_location} residents.</p>

<hr>
<p><strong>Best regards,</strong></p>
<p><strong>Michael Yessian</strong><br>
{settings.organization_operating_names}<br>
Reply-to: {settings.reply_to_email}<br>
{settings.contact_phone} (Text communication only)</p>
</body>
</html>
"""
        
        return plain_text.strip(), html_text.strip()
    
    @staticmethod
    def generate_follow_up(
        supplier_name: str,
        contact_person: Optional[str] = None,
        days_since_contact: int = 7
    ) -> tuple[str, str]:
        """Generate a follow-up email with proper signature."""
        
        greeting = f"Dear {contact_person}" if contact_person else f"Dear {supplier_name} Team"
        
        plain_text = f"""
{greeting},

I'm following up on my previous email regarding {settings.organization_operating_names}'s mission to help elderly and low-income families in {settings.organization_location}.

I wanted to check if you've had a chance to consider our request for material donations. We're still very much interested in partnering with {supplier_name} to provide essential exterior home repairs for vulnerable neighbors who cannot afford these services.

As a reminder, your material donation directly helps elderly residents stay safe in their homes and allows low-income families to avoid displacement. Additionally, donating excess inventory serves as a strategic tax write-off under IRS Section 170 guidelines, and we provide all necessary documentation for your corporate giving records.

If you have any questions or need additional information about our organization or the specific materials we need, please don't hesitate to reach out. I'm happy to share stories of families we've helped and coordinate logistics for material pickup or delivery.

We believe this partnership would make a meaningful difference in the lives of {settings.organization_location} residents who need it most.

Looking forward to hearing from you.

Best regards,

Michael Yessian
{settings.organization_operating_names}
Reply-to: {settings.reply_to_email}
{settings.contact_phone} (Text communication only)
"""
        
        html_text = f"""
<html>
<body>
<h2>{greeting},</h2>

<p>I'm following up on my previous email regarding <strong>{settings.organization_operating_names}</strong>'s mission to help elderly and low-income families in {settings.organization_location}.</p>

<p>I wanted to check if you've had a chance to consider our request for material donations. We're still very much interested in partnering with <strong>{supplier_name}</strong> to provide essential exterior home repairs for vulnerable neighbors who cannot afford these services.</p>

<p>As a reminder, your material donation directly helps elderly residents stay safe in their homes and allows low-income families to avoid displacement. Additionally, donating excess inventory serves as a strategic tax write-off under IRS Section 170 guidelines, and we provide all necessary documentation for your corporate giving records.</p>

<p>If you have any questions or need additional information about our organization or the specific materials we need, please don't hesitate to reach out. I'm happy to share stories of families we've helped and coordinate logistics for material pickup or delivery.</p>

<p>We believe this partnership would make a meaningful difference in the lives of {settings.organization_location} residents who need it most.</p>

<p>Looking forward to hearing from you.</p>

<hr>
<p><strong>Best regards,</strong></p>
<p><strong>Michael Yessian</strong><br>
{settings.organization_operating_names}<br>
Reply-to: {settings.reply_to_email}<br>
{settings.contact_phone} (Text communication only)</p>
</body>
</html>
"""
        
        return plain_text.strip(), html_text.strip()


class OutreachEngine:
    """Main outreach engine coordinating email operations."""
    
    def __init__(self):
        self.email_provider = self._get_email_provider()
        self.email_count = 0
        self.max_emails_per_hour = settings.max_emails_per_hour
        self.delay_between_emails = settings.delay_between_emails
    
    def _get_email_provider(self) -> EmailProvider:
        """Initialize the configured email provider."""
        if settings.email_provider == "smtp" and settings.smtp_username:
            return SMTPEmailProvider(
                host=settings.smtp_host or "smtp.gmail.com",
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls
            )
        elif settings.email_provider == "sendgrid" and settings.sendgrid_api_key:
            return SendGridEmailProvider(settings.sendgrid_api_key)
        elif settings.email_provider == "gmail" and settings.gmail_client_id:
            return GmailAPIProvider(
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret,
                refresh_token=settings.gmail_refresh_token
            )
        else:
            print(f"Warning: Email provider '{settings.email_provider}' not configured. Using dummy provider.")
            return DummyEmailProvider()
    
    async def send_donation_request(
        self,
        supplier_name: str,
        to_email: str,
        contact_person: Optional[str] = None,
        material_type: str = "building materials"
    ) -> bool:
        """Send a donation request email."""
        # Check rate limiting
        if self.email_count >= self.max_emails_per_hour:
            print("Rate limit reached for emails. Please wait.")
            return False
        
        # Generate email content
        subject = f"Material Donation Request - {settings.organization_name}"
        plain_body, html_body = EmailTemplate.generate_donation_request(
            supplier_name=supplier_name,
            contact_person=contact_person,
            material_type=material_type
        )
        
        # Send email
        success = await self.email_provider.send_email(
            to=to_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )
        
        if success:
            self.email_count += 1
            # Rate limiting delay
            if self.email_count < self.max_emails_per_hour:
                await asyncio.sleep(self.delay_between_emails)
        
        return success
    
    async def send_follow_up(
        self,
        supplier_name: str,
        to_email: str,
        contact_person: Optional[str] = None,
        days_since_contact: int = 7
    ) -> bool:
        """Send a follow-up email."""
        # Check rate limiting
        if self.email_count >= self.max_emails_per_hour:
            print("Rate limit reached for emails. Please wait.")
            return False
        
        # Generate email content
        subject = f"Following Up - Material Donation Request - {settings.organization_name}"
        plain_body, html_body = EmailTemplate.generate_follow_up(
            supplier_name=supplier_name,
            contact_person=contact_person,
            days_since_contact=days_since_contact
        )
        
        # Send email
        success = await self.email_provider.send_email(
            to=to_email,
            subject=subject,
            body=plain_body,
            html_body=html_body
        )
        
        if success:
            self.email_count += 1
            # Rate limiting delay
            if self.email_count < self.max_emails_per_hour:
                await asyncio.sleep(self.delay_between_emails)
        
        return success
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """Check for email replies."""
        return await self.email_provider.check_replies(since)
    
    def analyze_response(self, response_text: str) -> Dict[str, Any]:
        """Analyze an email response to determine interest level."""
        response_lower = response_text.lower()
        
        positive_indicators = [
            "interested", "would love to", "happy to help", "we can",
            "yes", "sure", "absolutely", "definitely", "count us in",
            "we'd be happy", "we would like", "support", "contribute"
        ]
        
        negative_indicators = [
            "not interested", "unable to", "cannot", "can't", "sorry",
            "unfortunately", "decline", "unable to help", "not possible"
        ]
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in response_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in response_lower)
        
        if positive_count > negative_count:
            interest_level = "high"
        elif negative_count > positive_count:
            interest_level = "low"
        else:
            interest_level = "neutral"
        
        return {
            "interest_level": interest_level,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "requires_manual_review": interest_level in ["neutral", "high"]
        }


class DummyEmailProvider(EmailProvider):
    """Dummy email provider for testing when no API is configured."""
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Simulate sending an email."""
        print(f"[DUMMY] Would send email to {to}")
        print(f"[DUMMY] Subject: {subject}")
        print(f"[DUMMY] Body preview: {body[:100]}...")
        return True
    
    async def check_replies(self, since: datetime) -> List[Dict[str, Any]]:
        """Return empty list for dummy provider."""
        return []


# Singleton instance
outreach_engine = OutreachEngine()