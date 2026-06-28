from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class DashboardMetrics(BaseModel):
    total_donors: int
    active_donors: int  # Donated in last 30 days
    total_donations: int
    total_revenue: float
    avg_donation_amount: float
    items_collected: int
    items_distributed: int
    revenue_this_month: float
    revenue_this_year: float
    donor_retention_rate: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

class DonorAnalytics(BaseModel):
    donor_id: str
    donor_name: str
    total_donations: int
    total_value: float
    avg_donation: float
    first_donation: datetime
    last_donation: datetime
    donation_frequency: str  # 'one-time', 'monthly', 'quarterly', 'annual'
    ltv_score: float  # Lifetime value score

class FinancialSummary(BaseModel):
    period: str
    total_revenue: float
    total_expenses: float
    net_income: float
    donation_breakdown: Dict[str, float]  # by category
    monthly_trend: List[Dict[str, Any]]    # month-over-month data

class InventoryReport(BaseModel):
    total_items: int
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    avg_days_in_inventory: float
    items_distributed_this_period: int
    items_expired_this_period: int

class ReportCreate(BaseModel):
    name: str
    report_type: str
    frequency: str
    recipients: List[str]
    parameters: Optional[Dict[str, Any]] = None

class ReportResponse(BaseModel):
    id: str
    name: str
    report_type: str
    frequency: str
    recipients: List[str]
    last_run_at: Optional[datetime] = None
    next_run_at: datetime
    is_active: bool
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime