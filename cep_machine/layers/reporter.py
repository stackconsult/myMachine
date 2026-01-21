"""
CEP Layer 7: Reporting Engine

Generate comprehensive performance reports for clients.
Aggregates data from all layers into actionable insights.

Container Alignment: Finance
Φ Contribution: +0.07

Input: Data from Layers 1-6
Output: Performance reports with metrics and recommendations
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class ReportType(Enum):
    """Types of reports."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class MetricCategory(Enum):
    """Categories of metrics."""
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    GBP = "gbp"


@dataclass
class Metric:
    """A performance metric."""
    name: str
    category: MetricCategory
    value: float
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    target: Optional[float] = None
    unit: str = ""
    trend: str = "neutral"  # up, down, neutral
    
    def __post_init__(self):
        if self.previous_value is not None and self.previous_value != 0:
            self.change_percent = ((self.value - self.previous_value) / self.previous_value) * 100
            if self.change_percent > 5:
                self.trend = "up"
            elif self.change_percent < -5:
                self.trend = "down"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "value": self.value,
            "previous_value": self.previous_value,
            "change_percent": self.change_percent,
            "target": self.target,
            "unit": self.unit,
            "trend": self.trend,
        }


@dataclass
class Insight:
    """An AI-generated insight."""
    category: str
    title: str
    description: str
    impact: str  # high, medium, low
    action_items: List[str]
    data_points: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "action_items": self.action_items,
            "data_points": self.data_points,
        }


@dataclass
class ClientReport:
    """A complete client report."""
    id: str
    client_id: str
    business_name: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    metrics: List[Metric] = field(default_factory=list)
    insights: List[Insight] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    phi_sync: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "business_name": self.business_name,
            "report_type": self.report_type.value,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
            "insights": [i.to_dict() for i in self.insights],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at.isoformat(),
            "phi_sync": self.phi_sync,
        }


@dataclass
class ReportingResult:
    """Result of report generation."""
    reports_generated: int
    metrics_analyzed: int
    insights_generated: int
    processing_time_seconds: float
    reports: List[ClientReport] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reports_generated": self.reports_generated,
            "metrics_analyzed": self.metrics_analyzed,
            "insights_generated": self.insights_generated,
            "processing_time_seconds": self.processing_time_seconds,
            "reports": [r.to_dict() for r in self.reports],
        }


class ReportingEngine:
    """
    Layer 7: Reporting Engine
    
    Generates comprehensive performance reports with AI insights.
    Aggregates data from all layers into actionable recommendations.
    """
    
    # Metric definitions
    METRIC_DEFINITIONS = {
        MetricCategory.SALES: [
            {"name": "Prospects Researched", "unit": "count"},
            {"name": "Pitches Sent", "unit": "count"},
            {"name": "Meetings Booked", "unit": "count"},
            {"name": "Conversion Rate", "unit": "%"},
            {"name": "Sales Cycle Days", "unit": "days"},
        ],
        MetricCategory.MARKETING: [
            {"name": "GBP Score", "unit": "points"},
            {"name": "GBP Views", "unit": "count"},
            {"name": "Website Clicks", "unit": "count"},
            {"name": "Phone Calls", "unit": "count"},
            {"name": "Direction Requests", "unit": "count"},
        ],
        MetricCategory.OPERATIONS: [
            {"name": "Onboarding Days", "unit": "days"},
            {"name": "Client Satisfaction", "unit": "score"},
            {"name": "Tasks Completed", "unit": "count"},
            {"name": "Response Time", "unit": "hours"},
        ],
        MetricCategory.FINANCE: [
            {"name": "Monthly Revenue", "unit": "$"},
            {"name": "Customer Acquisition Cost", "unit": "$"},
            {"name": "Customer Lifetime Value", "unit": "$"},
            {"name": "ROI", "unit": "%"},
        ],
        MetricCategory.GBP: [
            {"name": "Posts Published", "unit": "count"},
            {"name": "Photos Uploaded", "unit": "count"},
            {"name": "Reviews Responded", "unit": "count"},
            {"name": "Q&A Added", "unit": "count"},
        ],
    }
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4-turbo-preview", dry_run: bool = True):
        self.llm_provider = llm_provider
        self.model = model
        self.dry_run = dry_run
        self.llm = self._init_llm()
        self.reports: Dict[str, List[ClientReport]] = {}
    
    def _init_llm(self):
        """Initialize the LLM."""
        if not LLM_AVAILABLE:
            return None
        
        if self.llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return ChatAnthropic(
                    model=self.model or "claude-3-sonnet-20240229",
                    anthropic_api_key=api_key,
                )
        
        if self.llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(
                    model=self.model or "gpt-4-turbo-preview",
                    openai_api_key=api_key,
                )
        
        return None
    
    async def generate_reports(
        self,
        clients: List[Dict[str, Any]],
        report_type: ReportType = ReportType.WEEKLY,
        custom_period: Optional[Dict[str, datetime]] = None,
    ) -> ReportingResult:
        """
        Generate reports for multiple clients.
        
        Args:
            clients: List of client data with metrics from all layers
            report_type: Type of report to generate
            custom_period: Custom start/end dates for CUSTOM reports
        
        Returns:
            ReportingResult with all generated reports
        """
        start_time = datetime.now()
        
        print(f"[Layer 7] Generating {report_type.value} reports for {len(clients)} clients")
        
        result = ReportingResult(
            reports_generated=0,
            metrics_analyzed=0,
            insights_generated=0,
            processing_time_seconds=0.0,
        )
        
        # Determine period
        if custom_period:
            period_start = custom_period["start"]
            period_end = custom_period["end"]
        else:
            period_start, period_end = self._get_period_dates(report_type)
        
        # Generate report for each client
        for client in clients:
            report = await self._generate_client_report(
                client=client,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
            )
            
            if report:
                result.reports.append(report)
                result.reports_generated += 1
                result.metrics_analyzed += len(report.metrics)
                result.insights_generated += len(report.insights)
                
                # Store report
                if client["id"] not in self.reports:
                    self.reports[client["id"]] = []
                self.reports[client["id"]].append(report)
        
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        print(f"[Layer 7] ✓ Reports generated")
        print(f"  - Reports: {result.reports_generated}")
        print(f"  - Metrics: {result.metrics_analyzed}")
        print(f"  - Insights: {result.insights_generated}")
        print(f"  - Time: {result.processing_time_seconds:.1f}s")
        
        return result
    
    async def _generate_client_report(
        self,
        client: Dict[str, Any],
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime,
    ) -> Optional[ClientReport]:
        """Generate a report for a single client."""
        try:
            report = ClientReport(
                id=f"report_{client['id']}_{report_type.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                client_id=client["id"],
                business_name=client["business_name"],
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                phi_sync=client.get("phi_sync"),
            )
            
            # Collect metrics from all layers
            metrics = await self._collect_metrics(client, period_start, period_end)
            report.metrics.extend(metrics)
            
            # Generate AI insights
            insights = await self._generate_insights(report)
            report.insights.extend(insights)
            
            # Generate summary
            summary = await self._generate_summary(report)
            report.summary = summary
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(report)
            report.recommendations.extend(recommendations)
            
            return report
            
        except Exception as e:
            print(f"[Layer 7] Error generating report for {client['business_name']}: {e}")
            return None
    
    async def _collect_metrics(
        self,
        client: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
    ) -> List[Metric]:
        """Collect metrics from all layers."""
        metrics = []
        
        # Simulate collecting metrics from each layer
        # In production, this would query actual data
        
        # Layer 1: Prospects
        prospects_count = client.get("prospects_count", 0)
        metrics.append(Metric(
            name="Prospects Researched",
            category=MetricCategory.SALES,
            value=prospects_count,
            previous_value=prospects_count * 0.8,  # Simulate previous period
            unit="count",
        ))
        
        # Layer 2: Pitches
        pitches_count = client.get("pitches_count", 0)
        metrics.append(Metric(
            name="Pitches Sent",
            category=MetricCategory.SALES,
            value=pitches_count,
            previous_value=pitches_count * 0.9,
            unit="count",
        ))
        
        # Layer 3: Outreach
        meetings_count = client.get("meetings_count", 0)
        metrics.append(Metric(
            name="Meetings Booked",
            category=MetricCategory.SALES,
            value=meetings_count,
            previous_value=meetings_count * 0.7,
            unit="count",
        ))
        
        # Calculate conversion rate
        conversion_rate = (meetings_count / pitches_count * 100) if pitches_count > 0 else 0
        metrics.append(Metric(
            name="Conversion Rate",
            category=MetricCategory.SALES,
            value=conversion_rate,
            target=15.0,
            unit="%",
        ))
        
        # Layer 6: GBP metrics
        gbp_score = client.get("gbp_score", 0)
        metrics.append(Metric(
            name="GBP Score",
            category=MetricCategory.GBP,
            value=gbp_score,
            previous_value=gbp_score - 10,
            target=85.0,
            unit="points",
        ))
        
        gbp_views = client.get("gbp_views", 0)
        metrics.append(Metric(
            name="GBP Views",
            category=MetricCategory.MARKETING,
            value=gbp_views,
            previous_value=gbp_views * 0.8,
            unit="count",
        ))
        
        # Layer 5: Onboarding
        onboarding_days = client.get("onboarding_days", 14)
        metrics.append(Metric(
            name="Onboarding Days",
            category=MetricCategory.OPERATIONS,
            value=onboarding_days,
            target=10.0,
            unit="days",
        ))
        
        # Finance metrics
        monthly_revenue = client.get("monthly_revenue", 0)
        metrics.append(Metric(
            name="Monthly Revenue",
            category=MetricCategory.FINANCE,
            value=monthly_revenue,
            previous_value=monthly_revenue * 0.9,
            unit="$",
        ))
        
        cac = client.get("customer_acquisition_cost", 500)
        metrics.append(Metric(
            name="Customer Acquisition Cost",
            category=MetricCategory.FINANCE,
            value=cac,
            target=300.0,
            unit="$",
        ))
        
        return metrics
    
    async def _generate_insights(self, report: ClientReport) -> List[Insight]:
        """Generate AI insights from metrics."""
        insights = []
        
        # Find significant changes
        significant_metrics = [
            m for m in report.metrics
            if m.change_percent and abs(m.change_percent) > 10
        ]
        
        for metric in significant_metrics:
            if self.llm:
                insight = await self._llm_generate_insight(metric, report)
                insights.append(insight)
            else:
                # Fallback insights
                if metric.trend == "up" and metric.category == MetricCategory.SALES:
                    insights.append(Insight(
                        category="Sales Growth",
                        title=f"{metric.name} Increased",
                        description=f"{metric.name} increased by {metric.change_percent:.1f}% this period.",
                        impact="high",
                        action_items=["Analyze what drove the increase", "Replicate successful strategies"],
                        data_points=[f"{metric.name}: {metric.value} {metric.unit}"],
                    ))
                elif metric.trend == "down" and metric.category == MetricCategory.FINANCE:
                    insights.append(Insight(
                        category="Financial Alert",
                        title=f"{metric.name} Decreased",
                        description=f"{metric.name} decreased by {abs(metric.change_percent):.1f}% this period.",
                        impact="high",
                        action_items=["Investigate cause of decrease", "Implement corrective actions"],
                        data_points=[f"{metric.name}: {metric.value} {metric.unit}"],
                    ))
        
        # Add GBP insights
        gbp_metrics = [m for m in report.metrics if m.category == MetricCategory.GBP]
        if gbp_metrics:
            gbp_score = next((m for m in gbp_metrics if m.name == "GBP Score"), None)
            if gbp_score and gbp_score.value < 70:
                insights.append(Insight(
                    category="GBP Optimization",
                    title="Low GBP Score",
                    description="Your Google Business Profile score needs improvement.",
                    impact="medium",
                    action_items=["Add more photos", "Respond to reviews", "Post regular updates"],
                    data_points=[f"Current Score: {gbp_score.value}/100"],
                ))
        
        return insights
    
    async def _llm_generate_insight(self, metric: Metric, report: ClientReport) -> Insight:
        """Generate insight using LLM."""
        context = f"""
Business: {report.business_name}
Metric: {metric.name}
Current Value: {metric.value} {metric.unit}
Previous Value: {metric.previous_value} {metric.unit} if metric.previous_value else "N/A"
Change: {metric.change_percent:.1f}% if metric.change_percent else "N/A"
Trend: {metric.trend}
"""
        
        prompt = f"""Generate a business insight based on this metric data:

{context}

Requirements:
- Title: Clear and concise
- Description: Explain what happened and why it matters
- Impact: high, medium, or low
- Action Items: 2-3 specific recommendations
- Data Points: Reference the key numbers

Format: Return JSON with {{"title": "...", "description": "...", "impact": "...", "action_items": [...], "data_points": [...]}}"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            data = json.loads(response.content)
            
            return Insight(
                category=metric.category.value,
                title=data.get("title", ""),
                description=data.get("description", ""),
                impact=data.get("impact", "medium"),
                action_items=data.get("action_items", []),
                data_points=data.get("data_points", []),
            )
        except Exception as e:
            print(f"[Layer 7] LLM insight generation failed: {e}")
            # Return fallback
            return Insight(
                category=metric.category.value,
                title=f"{metric.name} Update",
                description=f"Metric changed by {metric.change_percent:.1f}% this period.",
                impact="medium",
                action_items=["Monitor trend", "Investigate drivers"],
                data_points=[f"{metric.name}: {metric.value} {metric.unit}"],
            )
    
    async def _generate_summary(self, report: ClientReport) -> str:
        """Generate report summary."""
        if self.llm:
            return await self._llm_generate_summary(report)
        else:
            # Fallback summary
            key_metrics = [m for m in report.metrics if m.category in [MetricCategory.SALES, MetricCategory.FINANCE]]
            summary_parts = []
            
            for metric in key_metrics[:3]:
                if metric.change_percent:
                    direction = "increased" if metric.trend == "up" else "decreased"
                    summary_parts.append(f"{metric.name} {direction} by {abs(metric.change_percent):.1f}%")
            
            return f"This period, {', '.join(summary_parts)}. Overall performance shows {'positive' if report.phi_sync and report.phi_sync > 0.7 else 'mixed'} results."
    
    async def _llm_generate_summary(self, report: ClientReport) -> str:
        """Generate summary using LLM."""
        metrics_summary = "\n".join([
            f"- {m.name}: {m.value} {m.unit} ({m.trend})"
            for m in report.metrics[:5]
        ])
        
        prompt = f"""Write a professional executive summary for this business report:

Business: {report.business_name}
Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}
Φ_sync: {report.phi_sync}

Key Metrics:
{metrics_summary}

Requirements:
- 3-4 sentences max
- Professional tone
- Highlight key achievements and challenges
- No bullet points

Format: Return only the summary text."""
        
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"[Layer 7] LLM summary generation failed: {e}")
            return "Report summary unavailable due to technical issues."
    
    async def _generate_recommendations(self, report: ClientReport) -> List[str]:
        """Generate recommendations based on report."""
        recommendations = []
        
        # Collect from insights
        for insight in report.insights:
            recommendations.extend(insight.action_items)
        
        # Add metric-based recommendations
        for metric in report.metrics:
            if metric.target and metric.value < metric.target * 0.8:
                if metric.name == "Conversion Rate":
                    recommendations.append("Improve pitch quality and follow-up timing")
                elif metric.name == "GBP Score":
                    recommendations.append("Complete GBP optimization tasks")
                elif metric.name == "Customer Acquisition Cost":
                    recommendations.append("Optimize marketing channels for better ROI")
        
        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:5]
    
    def _get_period_dates(self, report_type: ReportType) -> tuple[datetime, datetime]:
        """Get period start and end dates."""
        now = datetime.now()
        
        if report_type == ReportType.WEEKLY:
            start = now - timedelta(days=7)
            end = now
        elif report_type == ReportType.MONTHLY:
            start = now - timedelta(days=30)
            end = now
        elif report_type == ReportType.QUARTERLY:
            start = now - timedelta(days=90)
            end = now
        else:  # CUSTOM
            start = now - timedelta(days=30)
            end = now
        
        return start, end
    
    async def get_client_reports(
        self,
        client_id: str,
        report_type: Optional[ReportType] = None,
        limit: int = 10,
    ) -> List[ClientReport]:
        """Get reports for a specific client."""
        reports = self.reports.get(client_id, [])
        
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        
        # Sort by generated date (newest first)
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        
        return reports[:limit]


# Layer 7 Entry Point
async def run_layer(
    clients: List[Dict[str, Any]],
    report_type: str = "weekly",
    dry_run: bool = True,
) -> ReportingResult:
    """
    Main entry point for Layer 7: Reporting Engine
    
    Args:
        clients: List of client data with metrics
        report_type: Type of report (weekly, monthly, quarterly, custom)
        dry_run: If True, simulate external API calls
    
    Returns:
        ReportingResult with all generated reports
    """
    print(f"\n{'='*60}")
    print(f"[Layer 7] REPORTING ENGINE")
    print(f"Clients: {len(clients)}")
    print(f"Type: {report_type}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    # Convert string to enum
    report_type_enum = ReportType(report_type.lower())
    
    engine = ReportingEngine(dry_run=dry_run)
    result = await engine.generate_reports(clients, report_type_enum)
    
    print(f"\n[Layer 7] ✓ Complete")
    print(f"  - Reports: {result.reports_generated}")
    print(f"  - Metrics: {result.metrics_analyzed}")
    print(f"  - Insights: {result.insights_generated}")
    print(f"  - Processing time: {result.processing_time_seconds:.1f}s")
    
    return result


# Export
__all__ = [
    "Metric",
    "Insight",
    "ClientReport",
    "ReportingResult",
    "ReportingEngine",
    "ReportType",
    "MetricCategory",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Sample client data
    sample_clients = [
        {
            "id": "client_001",
            "business_name": "Test Dental Clinic",
            "prospects_count": 45,
            "pitches_count": 30,
            "meetings_count": 8,
            "gbp_score": 75,
            "gbp_views": 1250,
            "onboarding_days": 12,
            "monthly_revenue": 5000,
            "customer_acquisition_cost": 450,
            "phi_sync": 0.82,
        },
        {
            "id": "client_002",
            "business_name": "Test HVAC Company",
            "prospects_count": 30,
            "pitches_count": 20,
            "meetings_count": 5,
            "gbp_score": 68,
            "gbp_views": 800,
            "onboarding_days": 15,
            "monthly_revenue": 3500,
            "customer_acquisition_cost": 600,
            "phi_sync": 0.75,
        },
    ]
    
    report_type = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    dry_run = "--live" not in sys.argv
    
    result = asyncio.run(run_layer(sample_clients, report_type=report_type, dry_run=dry_run))
    
    print("\n" + "="*60)
    print("REPORT SUMMARY:")
    print("="*60)
    
    for report in result.reports:
        print(f"\n{report.business_name}")
        print(f"Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}")
        print(f"Φ_sync: {report.phi_sync:.2f}")
        print(f"\nSummary: {report.summary}")
        
        print(f"\nTop Metrics:")
        for metric in report.metrics[:3]:
            trend_icon = {"up": "📈", "down": "📉", "neutral": "➡️"}[metric.trend]
            print(f"  {trend_icon} {metric.name}: {metric.value} {metric.unit}")
        
        print(f"\nKey Insights:")
        for insight in report.insights[:2]:
            impact_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[insight.impact]
            print(f"  {impact_icon} {insight.title}")
        
        print(f"\nRecommendations:")
        for rec in report.recommendations[:2]:
            print(f"  • {rec}")
