from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from app.models.donor import Donor
from app.models.analytics import AnalyticsCache, ScheduledReport
from app.schemas.analytics import (
    DashboardMetrics, DonorAnalytics, FinancialSummary, InventoryReport
)
import json
import uuid

def get_utc_now():
    return datetime.now(timezone.utc)

class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DashboardMetrics:
        """Calculate comprehensive dashboard metrics"""
        
        if not start_date:
            start_date = get_utc_now() - timedelta(days=30)
        if not end_date:
            end_date = get_utc_now()
        
        # Check cache first
        cache_key = f"dashboard_{start_date.date()}_{end_date.date()}"
        cached = await self._get_cached_analytics(cache_key)
        if cached:
            return DashboardMetrics(**cached)
        
        # Calculate metrics
        metrics = await self._calculate_dashboard_metrics(start_date, end_date)
        
        # Cache results
        await self._cache_analytics(cache_key, metrics, expire_minutes=15)
        
        return DashboardMetrics(**metrics)
    
    async def _calculate_dashboard_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Core metrics calculation logic"""
        
        # Total donors
        total_donors_result = await self.session.execute(
            select(func.count(Donor.id))
        )
        total_donors = total_donors_result.scalar()
        
        # Active donors (donated in last 30 days)
        thirty_days_ago = get_utc_now() - timedelta(days=30)
        active_donors_result = await self.session.execute(
            select(func.count(Donor.id)).where(
                and_(
                    Donor.last_donation_date >= thirty_days_ago,
                    Donor.last_donation_date.isnot(None)
                )
            )
        )
        active_donors = active_donors_result.scalar()
        
        # Total donations and revenue
        revenue_result = await self.session.execute(
            select(
                func.count(Donor.id).label('count'),
                func.sum(Donor.total_value).label('total')
            )
        )
        revenue_data = revenue_result.first()
        total_donations = revenue_data.count or 0
        total_revenue = (revenue_data.total or 0) / 100  # Convert cents to dollars
        
        # Average donation
        avg_donation = total_revenue / total_donations if total_donations > 0 else 0
        
        # Items metrics (from existing items table)
        try:
            items_result = await self.session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_items,
                        COUNT(CASE WHEN status = 'distributed' THEN 1 END) as distributed
                    FROM items
                    WHERE posted_at BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            items_data = items_result.first()
        except Exception:
            # If items table doesn't exist or query fails
            items_data = type('obj', (object,), {'total_items': 0, 'distributed': 0})()
        
        # Monthly revenue
        month_start = get_utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = await self.session.execute(
            select(func.sum(Donor.total_value)).where(
                and_(
                    Donor.last_donation_date >= month_start,
                    Donor.last_donation_date.isnot(None)
                )
            )
        )
        monthly_revenue = (monthly_revenue_result.scalar() or 0) / 100
        
        # Yearly revenue
        year_start = get_utc_now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        yearly_revenue_result = await self.session.execute(
            select(func.sum(Donor.total_value)).where(
                and_(
                    Donor.last_donation_date >= year_start,
                    Donor.last_donation_date.isnot(None)
                )
            )
        )
        yearly_revenue = (yearly_revenue_result.scalar() or 0) / 100
        
        # Donor retention rate (simplified)
        retention_rate = (active_donors / total_donors * 100) if total_donors > 0 else 0
        
        return {
            "total_donors": total_donors,
            "active_donors": active_donors,
            "total_donations": total_donations,
            "total_revenue": total_revenue,
            "avg_donation_amount": avg_donation,
            "items_collected": items_data.total_items or 0,
            "items_distributed": items_data.distributed or 0,
            "revenue_this_month": monthly_revenue,
            "revenue_this_year": yearly_revenue,
            "donor_retention_rate": retention_rate,
            "period_start": start_date,
            "period_end": end_date
        }
    
    async def get_donor_analytics(self, donor_id: str) -> Optional[DonorAnalytics]:
        """Get detailed analytics for a specific donor"""
        
        donor_result = await self.session.execute(
            select(Donor).where(Donor.id == donor_id)
        )
        donor = donor_result.scalar_one_or_none()
        
        if not donor:
            return None
        
        # Calculate donation frequency
        donation_frequency = self._calculate_donation_frequency(donor)
        
        # Calculate LTV score
        ltv_score = self._calculate_ltv_score(donor)
        
        return DonorAnalytics(
            donor_id=donor.id,
            donor_name=donor.name or "Unknown",
            total_donations=donor.total_donations,
            total_value=donor.total_value / 100,
            avg_donation=(donor.total_value / donor.total_donations / 100) if donor.total_donations > 0 else 0,
            first_donation=donor.first_donation_date,
            last_donation=donor.last_donation_date,
            donation_frequency=donation_frequency,
            ltv_score=ltv_score
        )
    
    def _calculate_donation_frequency(self, donor: Donor) -> str:
        """Determine donation frequency pattern"""
        if donor.total_donations <= 1:
            return "one-time"
        
        if not donor.first_donation_date or not donor.last_donation_date:
            return "unknown"
        
        days_between = (donor.last_donation_date - donor.first_donation_date).days
        if days_between <= 0:
            return "unknown"
        
        avg_days = days_between / (donor.total_donations - 1)
        
        if avg_days <= 35:
            return "monthly"
        elif avg_days <= 100:
            return "quarterly"
        elif avg_days <= 365:
            return "annual"
        else:
            return "irregular"
    
    def _calculate_ltv_score(self, donor: Donor) -> float:
        """Calculate lifetime value score (0-100)"""
        if donor.total_donations == 0:
            return 0.0
        
        # Simple LTV scoring based on total value and frequency
        value_score = min(donor.total_value / 10000, 1.0) * 50  # Max 50 points for value
        frequency_score = min(donor.total_donations / 10, 1.0) * 30  # Max 30 points for frequency
        recency_score = 0  # Would be calculated based on last donation date
        
        return value_score + frequency_score + recency_score
    
    async def get_financial_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> FinancialSummary:
        """Generate financial summary report"""
        
        # This would query actual donation/expense tables
        # For now, returning a simplified version
        
        revenue_result = await self.session.execute(
            select(func.sum(Donor.total_value)).where(
                and_(
                    Donor.last_donation_date >= start_date,
                    Donor.last_donation_date <= end_date
                )
            )
        )
        total_revenue = (revenue_result.scalar() or 0) / 100
        
        return FinancialSummary(
            period=f"{start_date.date()} to {end_date.date()}",
            total_revenue=total_revenue,
            total_expenses=0.0,  # Would come from expense tracking
            net_income=total_revenue,
            donation_breakdown={},
            monthly_trend=[]
        )
    
    async def get_inventory_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> InventoryReport:
        """Generate inventory analytics report"""
        
        try:
            result = await self.session.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_items,
                        category,
                        source
                    FROM items
                    WHERE posted_at BETWEEN :start_date AND :end_date
                    GROUP BY category, source
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            total_items = 0
            by_category = {}
            by_source = {}
            
            for row in result:
                total_items += row.total_items
                if row.category:
                    by_category[row.category] = by_category.get(row.category, 0) + row.total_items
                if row.source:
                    by_source[row.source] = by_source.get(row.source, 0) + row.total_items
        except Exception:
            # If items table doesn't exist or query fails
            total_items = 0
            by_category = {}
            by_source = {}
        
        return InventoryReport(
            total_items=total_items,
            by_category=by_category,
            by_source=by_source,
            avg_days_in_inventory=0.0,
            items_distributed_this_period=0,
            items_expired_this_period=0
        )
    
    async def get_donations_report(self, start_date: datetime, end_date: datetime) -> str:
        """Generate a CSV report of all donations in the period"""
        import csv
        import io
        from app.models.donation import Donation

        query = select(Donation, Donor).join(Donor).where(
            and_(
                Donation.donation_date >= start_date,
                Donation.donation_date <= end_date
            )
        )
        result = await self.session.execute(query)
        rows = result.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Donor Name", "Email", "Type", "Amount ($)", "Description"])

        for donation, donor in rows:
            writer.writerow([
                donation.donation_date.strftime("%Y-%m-%d"),
                donor.name,
                donor.email,
                donation.donation_type,
                donation.amount / 100,
                donation.description or ""
            ])

        return output.getvalue()

    async def _get_cached_analytics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analytics if valid"""
        result = await self.session.execute(
            select(AnalyticsCache).where(AnalyticsCache.cache_key == cache_key)
        )
        cache = result.scalar_one_or_none()
        
        if cache and not cache.is_expired():
            return cache.data
        return None
    
    async def _cache_analytics(
        self,
        cache_key: str,
        data: Dict[str, Any],
        expire_minutes: int
    ):
        """Cache analytics results"""
        expires_at = get_utc_now() + timedelta(minutes=expire_minutes)
        
        cache = AnalyticsCache(
            id=str(uuid.uuid4()),
            cache_key=cache_key,
            data=data,
            expires_at=expires_at
        )
        
        self.session.add(cache)
        await self.session.commit()