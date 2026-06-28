from datetime import datetime
from typing import Optional
from pathlib import Path
import uuid
from jinja2 import Template
from app.models.receipt import Receipt
from app.models.donor import Donor

class ReceiptGenerator:
    def __init__(self, template_path: str = "app/templates/receipt_template.html"):
        self.template_path = template_path
        self.output_dir = Path("receipts")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_receipt_number(self) -> str:
        """Generate unique receipt number"""
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"RCP-{timestamp}-{unique_id}"
    
    async def generate_pdf(
        self,
        receipt: Receipt,
        donor: Donor,
        organization_info: dict
    ) -> str:
        """Generate PDF receipt from template"""
        
        # Load template
        try:
            with open(self.template_path, 'r') as f:
                template_content = f.read()
        except FileNotFoundError:
            # Use a simple fallback template if file doesn't exist
            template_content = self._get_fallback_template()
        
        template = Template(template_content)
        
        # Render HTML
        html_content = template.render(
            receipt_number=receipt.receipt_number,
            receipt_date=receipt.receipt_date.strftime("%B %d, %Y"),
            donor_name=donor.name or "Valued Donor",
            donor_address=donor.address or "",
            donor_city=donor.city or "",
            donor_state=donor.state or "",
            donor_zip=donor.zip_code or "",
            amount_cents=receipt.amount,
            amount_dollars=receipt.amount / 100,
            donation_date=receipt.donation_date.strftime("%B %d, %Y"),
            organization_name=organization_info.get("name", "Nonprofit Organization"),
            organization_address=organization_info.get("address", ""),
            tax_id=organization_info.get("tax_id", ""),
            current_year=datetime.now().year
        )
        
        # Generate PDF
        pdf_filename = f"{receipt.receipt_number}.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(str(pdf_path))
        except ImportError:
            # Fallback: save as HTML if weasyprint not available
            with open(pdf_path.with_suffix('.html'), 'w') as f:
                f.write(html_content)
            pdf_path = pdf_path.with_suffix('.html')
        
        return str(pdf_path)
    
    def _get_fallback_template(self) -> str:
        """Return a simple HTML template for receipt generation"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Donation Receipt</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .receipt-number { font-size: 18px; font-weight: bold; color: #333; }
                .organization { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
                .section { margin-bottom: 20px; }
                .label { font-weight: bold; }
                .amount { font-size: 24px; font-weight: bold; color: #2e7d32; }
                .footer { margin-top: 40px; text-align: center; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="organization">{{ organization_name }}</div>
                <div>{{ organization_address }}</div>
                {% if tax_id %}
                <div>Tax ID: {{ tax_id }}</div>
                {% endif %}
            </div>
            
            <div class="section">
                <div class="receipt-number">Receipt #{{ receipt_number }}</div>
                <div>Date: {{ receipt_date }}</div>
            </div>
            
            <div class="section">
                <div><span class="label">Donor:</span> {{ donor_name }}</div>
                <div>{{ donor_address }}</div>
                <div>{{ donor_city }}, {{ donor_state }} {{ donor_zip }}</div>
            </div>
            
            <div class="section">
                <div><span class="label">Donation Date:</span> {{ donation_date }}</div>
                <div><span class="label">Amount:</span> <span class="amount">${{ amount_dollars }}</span></div>
            </div>
            
            <div class="footer">
                <p>This receipt confirms your donation to {{ organization_name }}.</p>
                <p>Thank you for your generous support!</p>
                <p>© {{ current_year }} {{ organization_name }}</p>
            </div>
        </body>
        </html>
        """
    
    def generate_receipt_data(
        self,
        donor: Donor,
        amount: int,
        donation_date: datetime,
        organization_info: dict
    ) -> dict:
        """Prepare receipt data for template rendering"""
        return {
            "receipt_number": self.generate_receipt_number(),
            "receipt_date": datetime.utcnow(),
            "donor": donor,
            "amount": amount,
            "donation_date": donation_date,
            "organization": organization_info
        }