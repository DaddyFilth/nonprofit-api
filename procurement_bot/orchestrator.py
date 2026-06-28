"""
Main orchestrator for the autonomous material procurement and marketing bot.

Ties together all modules in a continuous loop:
Search -> Extract -> Email -> Track -> Market
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procurement_bot.config import settings
from procurement_bot.modules.database import db_manager
from procurement_bot.modules.search import supplier_searcher
from procurement_bot.modules.email import outreach_engine
from procurement_bot.modules.marketing import marketing_generator


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ProcurementOrchestrator:
    """Main orchestrator for the procurement bot."""
    
    def __init__(self):
        self.db = db_manager
        self.searcher = supplier_searcher
        self.emailer = outreach_engine
        self.marketer = marketing_generator
        self.running = False
        
        # Configuration
        self.material_types = [
            "commercial-grade driveway sealants",
            "treated lumber and hardware", 
            "vinyl siding cleaning solutions",
            "heavy-duty applicators",
            "exterior paint and primers",
            "weatherproofing materials"
        ]
        self.locations = [settings.organization_location, "Oklahoma", "Texas", "Arkansas"]
        self.max_new_suppliers_per_cycle = 10
        self.max_outreach_per_cycle = 5
    
    async def initialize(self):
        """Initialize the orchestrator."""
        logger.info("Initializing procurement bot orchestrator...")
        
        # Check if there's an active campaign
        active_campaign = await self.db.get_active_campaign()
        
        if not active_campaign:
            logger.info("No active campaign found. Creating a new campaign...")
            campaign = await self.db.create_campaign(
                name=f"{settings.organization_location} Elderly & Low-Income Family Home Repair Materials Procurement",
                description=f"Automated outreach to building material suppliers for {settings.organization_operating_names} mission of providing essential exterior home repair for elderly and low-income families at absolutely no cost",
                target_materials=str(self.material_types),
                target_region=settings.organization_location,
                start_date=datetime.now(timezone.utc),
            )
            logger.info(f"Created new campaign: {campaign.name} (ID: {campaign.id})")
        else:
            logger.info(f"Found active campaign: {active_campaign.name} (ID: {active_campaign.id})")
    
    async def search_and_extract_suppliers(self) -> List[Dict[str, Any]]:
        """Search for and extract supplier information."""
        logger.info("Starting supplier search and extraction...")
        
        new_suppliers = []
        
        # Search for different material types
        for material in self.material_types[:2]:  # Limit to 2 material types per cycle
            logger.info(f"Searching for {material} suppliers...")
            
            try:
                results = await self.searcher.find_and_extract_suppliers(
                    material_type=material,
                    location=settings.organization_location,
                    num_results=5,
                    scrape_contact_info=True
                )
                
                logger.info(f"Found {len(results)} potential suppliers for {material}")
                
                # Process results and add to database
                for result in results:
                    # Check if supplier already exists
                    existing = await self.db.get_supplier_by_website(result["link"])
                    if existing:
                        logger.debug(f"Supplier already exists: {result['link']}")
                        continue
                    
                    # Extract contact info
                    contact_info = result.get("contact_info", {})
                    emails = contact_info.get("emails", [])
                    primary_email = emails[0] if emails else None
                    
                    if not primary_email:
                        logger.debug(f"No email found for {result['link']}, skipping")
                        continue
                    
                    # Create supplier
                    supplier = await self.db.create_supplier(
                        name=result.get("title", "Unknown"),
                        email=primary_email,
                        website=result["link"],
                        company_name=contact_info.get("company_name"),
                        industry_focus=material,
                    )
                    
                    logger.info(f"Created new supplier: {supplier.name} ({supplier.email})")
                    new_suppliers.append(supplier)
                    
                    if len(new_suppliers) >= self.max_new_suppliers_per_cycle:
                        break
                
                if len(new_suppliers) >= self.max_new_suppliers_per_cycle:
                    break
                    
            except Exception as e:
                logger.error(f"Error searching for {material} suppliers: {e}")
        
        logger.info(f"Total new suppliers added: {len(new_suppliers)}")
        return new_suppliers
    
    async def perform_outreach(self, suppliers: List[Any]) -> int:
        """Perform email outreach to suppliers."""
        logger.info("Starting email outreach...")
        
        # Get active campaign
        campaign = await self.db.get_active_campaign()
        if not campaign:
            logger.error("No active campaign found for outreach")
            return 0
        
        outreach_count = 0
        
        for supplier in suppliers[:self.max_outreach_per_cycle]:
            try:
                # Add supplier to campaign if not already added
                await self.db.add_supplier_to_campaign(
                    campaign_id=campaign.id,
                    supplier_id=supplier.id
                )
                
                # Send donation request email
                success = await self.emailer.send_donation_request(
                    supplier_name=supplier.name,
                    to_email=supplier.email,
                    contact_person=supplier.contact_person,
                    material_type=supplier.industry_focus or "building materials"
                )
                
                if success:
                    # Update supplier status
                    await self.db.update_supplier_status(
                        supplier_id=supplier.id,
                        status="contacted",
                        last_contacted=datetime.now(timezone.utc),
                        contact_attempts=1,
                        last_outreach_method="email"
                    )
                    
                    outreach_count += 1
                    logger.info(f"Successfully contacted {supplier.name}")
                else:
                    logger.warning(f"Failed to contact {supplier.name}")
                
            except Exception as e:
                logger.error(f"Error during outreach to {supplier.name}: {e}")
        
        logger.info(f"Outreach completed: {outreach_count} emails sent")
        return outreach_count
    
    async def check_responses(self) -> int:
        """Check for email responses and update database."""
        logger.info("Checking for email responses...")
        
        # Check for replies from the last 24 hours
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        replies = await self.emailer.check_replies(since)
        
        logger.info(f"Found {len(replies)} email replies")
        
        processed_count = 0
        
        for reply in replies:
            try:
                # Extract sender email
                sender_email = reply.get("from", "")
                # Simple email extraction
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender_email)
                if email_match:
                    sender_email = email_match.group()
                
                # Find supplier by email
                supplier = await self.db.get_supplier_by_email(sender_email)
                if not supplier:
                    logger.debug(f"No supplier found for email: {sender_email}")
                    continue
                
                # Analyze response
                analysis = self.emailer.analyze_response(reply.get("body", ""))
                
                # Update supplier status based on analysis
                if analysis["interest_level"] == "high":
                    new_status = "interested"
                elif analysis["interest_level"] == "low":
                    new_status = "declined"
                else:
                    new_status = "contacted"  # Needs manual review
                
                await self.db.update_supplier_status(
                    supplier_id=supplier.id,
                    status=new_status,
                    response_received=True,
                    last_contacted=datetime.now(timezone.utc)
                )
                
                logger.info(f"Updated {supplier.name} status to {new_status}")
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing response: {e}")
        
        return processed_count
    
    async def generate_marketing_materials(self) -> int:
        """Generate marketing materials for interested suppliers."""
        logger.info("Generating marketing materials for interested suppliers...")
        
        # Get suppliers with "interested" status
        interested_suppliers = await self.db.get_suppliers_by_status("interested", limit=5)
        
        if not interested_suppliers:
            logger.info("No interested suppliers found")
            return 0
        
        generated_count = 0
        
        for supplier in interested_suppliers:
            try:
                # Generate marketing materials
                materials = await self.marketer.generate_all_marketing_materials(
                    supplier_name=supplier.name,
                    contact_person=supplier.contact_person,
                    donation_details="Material donation for elderly and low-income family home repair project",
                    impact_description="Helping elderly residents stay safe in their homes and allowing low-income families to remain in their homes instead of facing displacement",
                    project_description=f"Community initiative in {settings.organization_location} providing essential exterior home repair, property restoration, and maintenance for elderly and low-income families at absolutely no cost"
                )
                
                logger.info(f"Generated marketing materials for {supplier.name}")
                logger.debug(f"  Thank you email: {len(materials['thank_you_email'])} chars")
                logger.debug(f"  Social post: {len(materials['social_media_post'])} chars")
                logger.debug(f"  Press release: {len(materials['press_release'])} chars")
                
                # In a real implementation, you would save these to the database
                # or automatically send/post them
                
                generated_count += 1
                
            except Exception as e:
                logger.error(f"Error generating marketing materials for {supplier.name}: {e}")
        
        logger.info(f"Generated marketing materials for {generated_count} suppliers")
        return generated_count
    
    async def run_cycle(self) -> Dict[str, int]:
        """Run a single cycle of the procurement process."""
        logger.info("=" * 50)
        logger.info("Starting new procurement cycle")
        logger.info("=" * 50)
        
        results = {
            "new_suppliers": 0,
            "outreach_sent": 0,
            "responses_processed": 0,
            "marketing_generated": 0
        }
        
        try:
            # Step 1: Search and extract suppliers
            new_suppliers = await self.search_and_extract_suppliers()
            results["new_suppliers"] = len(new_suppliers)
            
            # Step 2: Perform outreach
            if new_suppliers:
                outreach_count = await self.perform_outreach(new_suppliers)
                results["outreach_sent"] = outreach_count
            
            # Step 3: Check for responses
            response_count = await self.check_responses()
            results["responses_processed"] = response_count
            
            # Step 4: Generate marketing materials
            marketing_count = await self.generate_marketing_materials()
            results["marketing_generated"] = marketing_count
            
            logger.info("Cycle completed successfully")
            logger.info(f"Results: {results}")
            
        except Exception as e:
            logger.error(f"Error during cycle: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    async def run_continuous(self, interval_minutes: int = 60):
        """Run the orchestrator in a continuous loop."""
        logger.info(f"Starting continuous mode with {interval_minutes} minute intervals")
        self.running = True
        
        try:
            while self.running:
                cycle_start = datetime.now(timezone.utc)
                
                # Run a single cycle
                await self.run_cycle()
                
                # Calculate sleep time
                cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
                sleep_time = max(0, (interval_minutes * 60) - cycle_duration)
                
                logger.info(f"Cycle completed in {cycle_duration:.2f} seconds")
                logger.info(f"Sleeping for {sleep_time:.2f} seconds until next cycle...")
                
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.running = False
    
    def stop(self):
        """Stop the continuous orchestrator."""
        self.running = False


async def main():
    """Main entry point."""
    logger.info("Starting Material Procurement Bot")
    
    # Initialize orchestrator
    orchestrator = ProcurementOrchestrator()
    await orchestrator.initialize()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Run in continuous mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        await orchestrator.run_continuous(interval_minutes=interval)
    else:
        # Run a single cycle
        results = await orchestrator.run_cycle()
        logger.info(f"Single cycle completed: {results}")


if __name__ == "__main__":
    asyncio.run(main())