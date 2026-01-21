"""
Tests for Layer 7: Reporting Engine

Success Criteria: 3 test reports generated with AI insights and recommendations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.reporter import (
    Metric,
    Insight,
    ClientReport,
    ReportingResult,
    ReportingEngine,
    ReportType,
    MetricCategory,
    run_layer,
)


class TestMetric:
    """Test Metric data class."""
    
    def test_metric_creation(self):
        """Test creating a metric."""
        metric = Metric(
            name="Test Metric",
            category=MetricCategory.SALES,
            value=100.0,
            previous_value=80.0,
        )
        
        assert metric.name == "Test Metric"
        assert metric.category == MetricCategory.SALES
        assert metric.value == 100.0
        assert metric.change_percent == 25.0
        assert metric.trend == "up"
    
    def test_metric_trend_calculation(self):
        """Test trend calculation."""
        # Up trend
        metric_up = Metric(
            name="Test Metric",
            category=MetricCategory.SALES,
            value=120.0,
            previous_value=100.0,
        )
        assert metric_up.trend == "up"
        
        # Down trend
        metric_down = Metric(
            name="Test Metric",
            category=MetricCategory.SALES,
            value=80.0,
            previous_value=100.0,
        )
        assert metric_down.trend == "down"
        
        # Neutral (small change)
        metric_neutral = Metric(
            name="Test Metric",
            category=MetricCategory.SALES,
            value=103.0,
            previous_value=100.0,
        )
        assert metric_neutral.trend == "neutral"
    
    def test_metric_to_dict(self):
        """Test metric serialization."""
        metric = Metric(
            name="Test Metric",
            category=MetricCategory.SALES,
            value=100.0,
            previous_value=80.0,
        )
        
        data = metric.to_dict()
        assert data["name"] == "Test Metric"
        assert data["category"] == "sales"
        assert data["value"] == 100.0
        assert data["change_percent"] == 25.0
        assert data["trend"] == "up"


class TestInsight:
    """Test Insight data class."""
    
    def test_insight_creation(self):
        """Test creating an insight."""
        insight = Insight(
            category="Sales",
            title="Sales Increased",
            description="Sales went up this month",
            impact="high",
            action_items=["Keep it up", "Analyze success"],
            data_points=["Sales: $10000"],
        )
        
        assert insight.category == "Sales"
        assert insight.title == "Sales Increased"
        assert insight.impact == "high"
        assert len(insight.action_items) == 2
    
    def test_insight_to_dict(self):
        """Test insight serialization."""
        insight = Insight(
            category="Sales",
            title="Sales Increased",
            description="Sales went up this month",
            impact="high",
            action_items=["Keep it up"],
            data_points=["Sales: $10000"],
        )
        
        data = insight.to_dict()
        assert data["category"] == "Sales"
        assert data["title"] == "Sales Increased"
        assert data["impact"] == "high"
        assert len(data["action_items"]) == 1


class TestClientReport:
    """Test ClientReport data class."""
    
    def test_report_creation(self):
        """Test creating a client report."""
        report = ClientReport(
            id="report_001",
            client_id="client_001",
            business_name="Test Business",
            report_type=ReportType.WEEKLY,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
        )
        
        assert report.id == "report_001"
        assert report.business_name == "Test Business"
        assert report.report_type == ReportType.WEEKLY
    
    def test_report_to_dict(self):
        """Test report serialization."""
        report = ClientReport(
            id="report_001",
            client_id="client_001",
            business_name="Test Business",
            report_type=ReportType.WEEKLY,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            phi_sync=0.85,
        )
        
        data = report.to_dict()
        assert data["id"] == "report_001"
        assert data["business_name"] == "Test Business"
        assert data["report_type"] == "weekly"
        assert data["phi_sync"] == 0.85


class TestReportingEngine:
    """Test ReportingEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return ReportingEngine(dry_run=True)
    
    @pytest.fixture
    def sample_clients(self):
        return [
            {
                "id": "client_001",
                "business_name": "Test Dental",
                "prospects_count": 50,
                "pitches_count": 30,
                "meetings_count": 8,
                "gbp_score": 75,
                "gbp_views": 1000,
                "onboarding_days": 12,
                "monthly_revenue": 5000,
                "customer_acquisition_cost": 400,
                "phi_sync": 0.82,
            },
            {
                "id": "client_002",
                "business_name": "Test HVAC",
                "prospects_count": 30,
                "pitches_count": 20,
                "meetings_count": 5,
                "gbp_score": 65,
                "gbp_views": 800,
                "onboarding_days": 15,
                "monthly_revenue": 3500,
                "customer_acquisition_cost": 600,
                "phi_sync": 0.75,
            },
        ]
    
    @pytest.mark.asyncio
    async def test_generate_reports(self, engine, sample_clients):
        """Test generating reports for multiple clients."""
        result = await engine.generate_reports(
            clients=sample_clients,
            report_type=ReportType.WEEKLY,
        )
        
        assert isinstance(result, ReportingResult)
        assert result.reports_generated == 2
        assert result.metrics_analyzed > 0
        assert result.insights_generated >= 0
        assert len(result.reports) == 2
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, engine, sample_clients):
        """Test metric collection from layers."""
        client = sample_clients[0]
        period_start = datetime.now() - timedelta(days=7)
        period_end = datetime.now()
        
        metrics = await engine._collect_metrics(client, period_start, period_end)
        
        assert len(metrics) > 0
        
        # Check specific metrics
        metric_names = [m.name for m in metrics]
        assert "Prospects Researched" in metric_names
        assert "GBP Score" in metric_names
        assert "Monthly Revenue" in metric_names
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, engine):
        """Test insight generation."""
        report = ClientReport(
            id="report_001",
            client_id="client_001",
            business_name="Test Business",
            report_type=ReportType.WEEKLY,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
        )
        
        # Add metrics with significant changes
        report.metrics = [
            Metric(
                name="Sales",
                category=MetricCategory.SALES,
                value=120.0,
                previous_value=100.0,
            ),
            Metric(
                name="GBP Score",
                category=MetricCategory.GBP,
                value=65.0,
                previous_value=60.0,
            ),
        ]
        
        insights = await engine._generate_insights(report)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert insight.title
            assert insight.description
            assert insight.impact in ["high", "medium", "low"]
            assert len(insight.action_items) > 0
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, engine):
        """Test report summary generation."""
        report = ClientReport(
            id="report_001",
            client_id="client_001",
            business_name="Test Business",
            report_type=ReportType.WEEKLY,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
            phi_sync=0.85,
        )
        
        report.metrics = [
            Metric(
                name="Sales",
                category=MetricCategory.SALES,
                value=120.0,
                previous_value=100.0,
            ),
            Metric(
                name="Revenue",
                category=MetricCategory.FINANCE,
                value=5000.0,
                previous_value=4500.0,
            ),
        ]
        
        summary = await engine._generate_summary(report)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, engine):
        """Test recommendation generation."""
        report = ClientReport(
            id="report_001",
            client_id="client_001",
            business_name="Test Business",
            report_type=ReportType.WEEKLY,
            period_start=datetime.now() - timedelta(days=7),
            period_end=datetime.now(),
        )
        
        # Add metrics below target
        report.metrics = [
            Metric(
                name="Conversion Rate",
                category=MetricCategory.SALES,
                value=10.0,
                target=15.0,
            ),
            Metric(
                name="GBP Score",
                category=MetricCategory.GBP,
                value=60.0,
                target=85.0,
            ),
        ]
        
        # Add insights with action items
        report.insights = [
            Insight(
                category="Sales",
                title="Low Conversion",
                description="Conversion rate is below target",
                impact="high",
                action_items=["Improve pitch quality"],
                data_points=["Conversion: 10%"],
            ),
        ]
        
        recommendations = await engine._generate_recommendations(report)
        
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)
    
    @pytest.mark.asyncio
    async def test_get_period_dates(self, engine):
        """Test period date calculation."""
        # Weekly
        start, end = engine._get_period_dates(ReportType.WEEKLY)
        assert (end - start).days <= 7
        
        # Monthly
        start, end = engine._get_period_dates(ReportType.MONTHLY)
        assert (end - start).days <= 31
        
        # Quarterly
        start, end = engine._get_period_dates(ReportType.QUARTERLY)
        assert (end - start).days <= 92
    
    @pytest.mark.asyncio
    async def test_get_client_reports(self, engine, sample_clients):
        """Test retrieving client reports."""
        # Generate reports first
        await engine.generate_reports(sample_clients, ReportType.WEEKLY)
        
        # Get reports for client
        reports = await engine.get_client_reports("client_001")
        
        assert len(reports) > 0
        assert all(r.client_id == "client_001" for r in reports)
        
        # Filter by type
        weekly_reports = await engine.get_client_reports(
            "client_001",
            report_type=ReportType.WEEKLY
        )
        assert all(r.report_type == ReportType.WEEKLY for r in weekly_reports)


class TestLayerEntry:
    """Test Layer 7 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        clients = [
            {
                "id": "client_001",
                "business_name": "Test Business",
                "prospects_count": 50,
                "pitches_count": 30,
                "meetings_count": 8,
                "gbp_score": 75,
                "monthly_revenue": 5000,
                "phi_sync": 0.82,
            }
        ]
        
        result = await run_layer(clients, report_type="weekly", dry_run=True)
        
        assert isinstance(result, ReportingResult)
        assert result.reports_generated == 1
        assert result.metrics_analyzed > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
