"""
CEP Containers - Core Business Container Classes

Container-Event Physics (CEP) defines three primary containers:
- Sales Container (daily timescale)
- Operations Container (hourly timescale)
- Finance Container (weekly timescale)

Each container tracks its own metrics and contributes to system coherence (Φ_sync).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ContainerType(Enum):
    SALES = "sales"
    OPERATIONS = "operations"
    FINANCE = "finance"


class Timescale(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class ContainerMetrics:
    """Metrics tracked by each container."""
    conversion_rate: float = 0.0
    throughput: float = 0.0
    efficiency: float = 0.0
    error_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversion_rate": self.conversion_rate,
            "throughput": self.throughput,
            "efficiency": self.efficiency,
            "error_rate": self.error_rate,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class CEPContainer:
    """Base class for CEP containers."""
    
    name: str
    container_type: ContainerType
    timescale: Timescale
    weight: float = 0.33
    metrics: ContainerMetrics = field(default_factory=ContainerMetrics)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event in this container."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "container": self.name,
        }
        self.events.append(event)
    
    def update_metrics(self, **kwargs) -> None:
        """Update container metrics."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        self.metrics.last_updated = datetime.now()
    
    def calculate_health(self) -> float:
        """Calculate container health score (0.0 to 1.0)."""
        # Health = (conversion + efficiency) / 2 - error_rate
        health = (self.metrics.conversion_rate + self.metrics.efficiency) / 2
        health -= self.metrics.error_rate
        return max(0.0, min(1.0, health))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.container_type.value,
            "timescale": self.timescale.value,
            "weight": self.weight,
            "metrics": self.metrics.to_dict(),
            "health": self.calculate_health(),
            "event_count": len(self.events),
        }


class SalesContainer(CEPContainer):
    """
    Sales Container - Daily Timescale
    
    Tracks:
    - Prospect research volume
    - Pitch generation rate
    - Outreach success rate
    - Booking conversion rate
    """
    
    def __init__(self):
        super().__init__(
            name="Sales",
            container_type=ContainerType.SALES,
            timescale=Timescale.DAILY,
            weight=0.33,
        )
        self.prospects_researched: int = 0
        self.pitches_generated: int = 0
        self.emails_sent: int = 0
        self.bookings_created: int = 0
    
    def record_prospect(self, prospect_data: Dict[str, Any]) -> None:
        """Record a new prospect researched."""
        self.prospects_researched += 1
        self.record_event("prospect_researched", prospect_data)
        self._update_conversion_rate()
    
    def record_pitch(self, pitch_data: Dict[str, Any]) -> None:
        """Record a pitch generated."""
        self.pitches_generated += 1
        self.record_event("pitch_generated", pitch_data)
        self._update_conversion_rate()
    
    def record_outreach(self, outreach_data: Dict[str, Any]) -> None:
        """Record an outreach email sent."""
        self.emails_sent += 1
        self.record_event("email_sent", outreach_data)
        self._update_conversion_rate()
    
    def record_booking(self, booking_data: Dict[str, Any]) -> None:
        """Record a booking created."""
        self.bookings_created += 1
        self.record_event("booking_created", booking_data)
        self._update_conversion_rate()
    
    def _update_conversion_rate(self) -> None:
        """Update conversion rate based on funnel metrics."""
        if self.prospects_researched > 0:
            self.metrics.conversion_rate = self.bookings_created / self.prospects_researched
        if self.emails_sent > 0:
            self.metrics.throughput = self.emails_sent


class OpsContainer(CEPContainer):
    """
    Operations Container - Hourly Timescale
    
    Tracks:
    - Onboarding completion rate
    - GBP optimization success
    - Report generation
    - System automation level
    """
    
    def __init__(self):
        super().__init__(
            name="Operations",
            container_type=ContainerType.OPERATIONS,
            timescale=Timescale.HOURLY,
            weight=0.34,
        )
        self.clients_onboarded: int = 0
        self.gbp_optimizations: int = 0
        self.reports_generated: int = 0
        self.automation_level: float = 0.0
    
    def record_onboarding(self, client_data: Dict[str, Any]) -> None:
        """Record a client onboarded."""
        self.clients_onboarded += 1
        self.record_event("client_onboarded", client_data)
        self._update_efficiency()
    
    def record_gbp_optimization(self, optimization_data: Dict[str, Any]) -> None:
        """Record a GBP optimization completed."""
        self.gbp_optimizations += 1
        self.record_event("gbp_optimized", optimization_data)
        self._update_efficiency()
    
    def record_report(self, report_data: Dict[str, Any]) -> None:
        """Record a report generated."""
        self.reports_generated += 1
        self.record_event("report_generated", report_data)
    
    def set_automation_level(self, level: float) -> None:
        """Set the current automation level (0.0 to 1.0)."""
        self.automation_level = max(0.0, min(1.0, level))
        self.metrics.efficiency = self.automation_level
    
    def _update_efficiency(self) -> None:
        """Update efficiency based on operations metrics."""
        total_ops = self.clients_onboarded + self.gbp_optimizations
        if total_ops > 0:
            self.metrics.throughput = total_ops


class FinanceContainer(CEPContainer):
    """
    Finance Container - Weekly Timescale
    
    Tracks:
    - MRR (Monthly Recurring Revenue)
    - Customer LTV
    - Profit margins
    - Payment success rate
    """
    
    def __init__(self):
        super().__init__(
            name="Finance",
            container_type=ContainerType.FINANCE,
            timescale=Timescale.WEEKLY,
            weight=0.33,
        )
        self.mrr: float = 0.0
        self.total_revenue: float = 0.0
        self.total_costs: float = 0.0
        self.customer_count: int = 0
        self.payment_success_count: int = 0
        self.payment_total_count: int = 0
    
    def record_payment(self, amount: float, success: bool = True) -> None:
        """Record a payment received."""
        self.payment_total_count += 1
        if success:
            self.payment_success_count += 1
            self.total_revenue += amount
        self.record_event("payment", {"amount": amount, "success": success})
        self._update_metrics()
    
    def record_customer(self, mrr_contribution: float) -> None:
        """Record a new customer added."""
        self.customer_count += 1
        self.mrr += mrr_contribution
        self.record_event("customer_added", {"mrr": mrr_contribution})
        self._update_metrics()
    
    def record_cost(self, amount: float, category: str) -> None:
        """Record a cost incurred."""
        self.total_costs += amount
        self.record_event("cost", {"amount": amount, "category": category})
        self._update_metrics()
    
    def _update_metrics(self) -> None:
        """Update finance metrics."""
        # Profit margin
        if self.total_revenue > 0:
            self.metrics.efficiency = (self.total_revenue - self.total_costs) / self.total_revenue
        
        # Payment success rate
        if self.payment_total_count > 0:
            self.metrics.conversion_rate = self.payment_success_count / self.payment_total_count
        
        self.metrics.throughput = self.mrr
    
    def get_profit(self) -> float:
        """Get current profit."""
        return self.total_revenue - self.total_costs
    
    def get_ltv(self) -> float:
        """Get average customer LTV."""
        if self.customer_count > 0:
            return self.total_revenue / self.customer_count
        return 0.0
