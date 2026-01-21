"""
Reporting Engine Agent - Layer 7
Generates dynamic dashboards and reports using AG-UI protocol
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import json

# CopilotKit imports
from deepagents import create_deep_agent, DeepAgent
from copilotkit.langchain import copilotkit_emit_state
from copilotkit.agui import AGUI

# CEP Machine imports
from cep_machine.layers.reporter import Reporter
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class ReportingEngineAgent:
    """Agent for generating dynamic reports and dashboards"""
    
    def __init__(self):
        self.reporter = Reporter()
        self.db = get_database()
        self.cache = get_cache()
    
    @AGUI
    async def generate_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic dashboard using AG-UI protocol"""
        # Collect data from all layers
        data_sources = dashboard_config.get("data_sources", ["all"])
        timeframe = dashboard_config.get("timeframe", "30d")
        
        # Fetch metrics from each layer
        all_metrics = {}
        
        if "prospects" in data_sources or "all" in data_sources:
            all_metrics["prospects"] = await self._fetch_prospect_metrics(timeframe)
        
        if "conversions" in data_sources or "all" in data_sources:
            all_metrics["conversions"] = await self._fetch_conversion_metrics(timeframe)
        
        if "outreach" in data_sources or "all" in data_sources:
            all_metrics["outreach"] = await self._fetch_outreach_metrics(timeframe)
        
        if "bookings" in data_sources or "all" in data_sources:
            all_metrics["bookings"] = await self._fetch_booking_metrics(timeframe)
        
        if "revenue" in data_sources or "all" in data_sources:
            all_metrics["revenue"] = await self._fetch_revenue_metrics(timeframe)
        
        # Generate dashboard components
        dashboard = {
            "type": "dashboard",
            "title": dashboard_config.get("title", "CEP Machine Dashboard"),
            "layout": dashboard_config.get("layout", "grid"),
            "components": await self._generate_dashboard_components(all_metrics, dashboard_config),
            "refresh_interval": dashboard_config.get("refresh_interval", 60),
            "generated_at": datetime.now().isoformat()
        }
        
        # Store dashboard configuration
        await self.db.create("dashboards", {
            "id": dashboard_config.get("id", f"dash_{datetime.now().timestamp()}"),
            "config": dashboard_config,
            "dashboard": dashboard,
            "created_at": datetime.now().isoformat()
        })
        
        # Emit dashboard state for real-time updates
        await copilotkit_emit_state(
            {
                "type": "dashboard_generated",
                "data": dashboard
            },
            {"channel": "dashboard_updates"}
        )
        
        return dashboard
    
    async def generate_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed report"""
        report_type = report_config.get("type", "summary")
        timeframe = report_config.get("timeframe", "30d")
        format_type = report_config.get("format", "json")
        
        # Collect report data
        report_data = await self._collect_report_data(report_type, timeframe)
        
        # Generate report sections
        report = {
            "id": f"report_{datetime.now().timestamp()}",
            "type": report_type,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat(),
            "sections": await self._generate_report_sections(report_data, report_type),
            "summary": await self._generate_report_summary(report_data),
            "insights": await self._generate_report_insights(report_data)
        }
        
        # Format report
        if format_type == "pdf":
            report["download_url"] = await self._generate_pdf_report(report)
        elif format_type == "excel":
            report["download_url"] = await self._generate_excel_report(report)
        
        # Store report
        await self.db.create("reports", report)
        
        # Send report notification
        await self._send_report_notification(report)
        
        return report
    
    async def get_real_time_metrics(self, metrics_request: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard"""
        metric_types = metrics_request.get("metrics", ["all"])
        
        # Fetch real-time data
        real_time_data = {}
        
        for metric_type in metric_types:
            if metric_type == "active_prospects":
                real_time_data["active_prospects"] = await self._get_active_prospects_count()
            elif metric_type == "conversion_rate":
                real_time_data["conversion_rate"] = await self._get_current_conversion_rate()
            elif metric_type == "outreach_sent":
                real_time_data["outreach_sent"] = await self._get_today_outreach_count()
            elif metric_type == "meetings_scheduled":
                real_time_data["meetings_scheduled"] = await self._get_today_meetings()
            elif metric_type == "revenue_today":
                real_time_data["revenue_today"] = await self._get_today_revenue()
        
        # Emit real-time update
        await copilotkit_emit_state(
            {
                "type": "real_time_metrics",
                "data": real_time_data,
                "timestamp": datetime.now().isoformat()
            },
            {"channel": "real_time_metrics"}
        )
        
        return real_time_data
    
    async def schedule_report(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule recurring report generation"""
        schedule = {
            "id": f"schedule_{datetime.now().timestamp()}",
            "report_type": schedule_config.get("report_type"),
            "frequency": schedule_config.get("frequency", "weekly"),
            "recipients": schedule_config.get("recipients", []),
            "next_run": self._calculate_next_run(schedule_config.get("frequency")),
            "config": schedule_config,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Store schedule
        await self.db.create("report_schedules", schedule)
        
        # Set up scheduler task
        await self._setup_scheduled_task(schedule)
        
        return schedule
    
    # Helper methods
    async def _fetch_prospect_metrics(self, timeframe: str) -> Dict:
        """Fetch prospect-related metrics"""
        # Mock implementation - fetch from database
        return {
            "total_prospects": 150,
            "new_prospects": 25,
            "prospects_by_source": {
                "website": 60,
                "referral": 40,
                "cold_outreach": 30,
                "social": 20
            },
            "prospects_by_status": {
                "new": 50,
                "contacted": 40,
                "qualified": 35,
                "converted": 25
            }
        }
    
    async def _fetch_conversion_metrics(self, timeframe: str) -> Dict:
        """Fetch conversion metrics"""
        return {
            "conversion_rate": 0.167,  # 16.7%
            "total_conversions": 25,
            "conversion_funnel": {
                "prospects": 150,
                "qualified": 80,
                "proposals_sent": 50,
                "closed_deals": 25
            },
            "average_deal_size": 5000,
            "sales_cycle_days": 45
        }
    
    async def _fetch_outreach_metrics(self, timeframe: str) -> Dict:
        """Fetch outreach metrics"""
        return {
            "emails_sent": 500,
            "emails_opened": 300,
            "emails_replied": 75,
            "calls_made": 100,
            "calls_connected": 60,
            "response_rate": 0.15
        }
    
    async def _fetch_booking_metrics(self, timeframe: str) -> Dict:
        """Fetch booking metrics"""
        return {
            "meetings_scheduled": 40,
            "meetings_completed": 35,
            "meetings_cancelled": 5,
            "show_rate": 0.875,
            "average_meeting_duration": 45
        }
    
    async def _fetch_revenue_metrics(self, timeframe: str) -> Dict:
        """Fetch revenue metrics"""
        return {
            "total_revenue": 125000,
            "recurring_revenue": 75000,
            "new_revenue": 50000,
            "revenue_by_service": {
                "consulting": 50000,
                "implementation": 40000,
                "support": 35000
            },
            "mrr_growth": 0.12  # 12% growth
        }
    
    async def _generate_dashboard_components(self, metrics: Dict, config: Dict) -> List[Dict]:
        """Generate dashboard components based on metrics"""
        components = []
        
        # KPI Cards
        if config.get("show_kpis", True):
            components.extend([
                {
                    "type": "kpi_card",
                    "title": "Total Prospects",
                    "value": metrics["prospects"]["total_prospects"],
                    "change": "+15%",
                    "trend": "up"
                },
                {
                    "type": "kpi_card",
                    "title": "Conversion Rate",
                    "value": f"{metrics['conversions']['conversion_rate'] * 100:.1f}%",
                    "change": "+2.3%",
                    "trend": "up"
                },
                {
                    "type": "kpi_card",
                    "title": "Total Revenue",
                    "value": f"${metrics['revenue']['total_revenue']:,}",
                    "change": "+18%",
                    "trend": "up"
                },
                {
                    "type": "kpi_card",
                    "title": "Meetings This Month",
                    "value": metrics["bookings"]["meetings_scheduled"],
                    "change": "+5",
                    "trend": "up"
                }
            ])
        
        # Charts
        if config.get("show_charts", True):
            components.extend([
                {
                    "type": "line_chart",
                    "title": "Prospect Trend",
                    "data": await self._format_chart_data(metrics["prospects"], "trend"),
                    "x_axis": "date",
                    "y_axis": "count"
                },
                {
                    "type": "bar_chart",
                    "title": "Revenue by Service",
                    "data": await self._format_chart_data(metrics["revenue"], "by_service"),
                    "x_axis": "service",
                    "y_axis": "revenue"
                },
                {
                    "type": "pie_chart",
                    "title": "Prospects by Source",
                    "data": await self._format_chart_data(metrics["prospects"], "by_source")
                },
                {
                    "type": "funnel_chart",
                    "title": "Conversion Funnel",
                    "data": metrics["conversions"]["conversion_funnel"]
                }
            ])
        
        # Tables
        if config.get("show_tables", True):
            components.append({
                "type": "data_table",
                "title": "Recent Activities",
                "columns": ["Date", "Activity", "Prospect", "Status"],
                "data": await self._get_recent_activities(),
                "sortable": True,
                "filterable": True
            })
        
        return components
    
    async def _collect_report_data(self, report_type: str, timeframe: str) -> Dict:
        """Collect data for report generation"""
        # Implementation varies by report type
        if report_type == "summary":
            return {
                "prospects": await self._fetch_prospect_metrics(timeframe),
                "conversions": await self._fetch_conversion_metrics(timeframe),
                "revenue": await self._fetch_revenue_metrics(timeframe)
            }
        elif report_type == "detailed":
            return {
                "all_metrics": {
                    "prospects": await self._fetch_prospect_metrics(timeframe),
                    "conversions": await self._fetch_conversion_metrics(timeframe),
                    "outreach": await self._fetch_outreach_metrics(timeframe),
                    "bookings": await self._fetch_booking_metrics(timeframe),
                    "revenue": await self._fetch_revenue_metrics(timeframe)
                }
            }
        
        return {}
    
    async def _generate_report_sections(self, data: Dict, report_type: str) -> List[Dict]:
        """Generate report sections"""
        sections = []
        
        if report_type == "summary":
            sections = [
                {
                    "title": "Executive Summary",
                    "content": await self._generate_executive_summary(data),
                    "type": "text"
                },
                {
                    "title": "Key Metrics",
                    "content": data,
                    "type": "metrics"
                }
            ]
        elif report_type == "detailed":
            sections = [
                {
                    "title": "Prospect Analysis",
                    "content": data["all_metrics"]["prospects"],
                    "type": "analysis"
                },
                {
                    "title": "Conversion Analysis",
                    "content": data["all_metrics"]["conversions"],
                    "type": "analysis"
                },
                {
                    "title": "Revenue Analysis",
                    "content": data["all_metrics"]["revenue"],
                    "type": "analysis"
                }
            ]
        
        return sections
    
    async def _generate_report_summary(self, data: Dict) -> Dict:
        """Generate report summary"""
        return {
            "total_prospects": data.get("prospects", {}).get("total_prospects", 0),
            "conversion_rate": data.get("conversions", {}).get("conversion_rate", 0),
            "total_revenue": data.get("revenue", {}).get("total_revenue", 0),
            "key_insights": await self._generate_key_insights(data)
        }
    
    async def _generate_report_insights(self, data: Dict) -> List[Dict]:
        """Generate insights from report data"""
        insights = []
        
        # Analyze trends and patterns
        if data.get("conversions", {}).get("conversion_rate", 0) > 0.15:
            insights.append({
                "type": "positive",
                "title": "Strong Conversion Performance",
                "description": "Conversion rate exceeds industry average"
            })
        
        return insights
    
    async def _generate_executive_summary(self, data: Dict) -> str:
        """Generate executive summary text"""
        return f"""
        During this period, we generated {data.get('prospects', {}).get('total_prospects', 0)} prospects
        with a conversion rate of {data.get('conversions', {}).get('conversion_rate', 0) * 100:.1f}%.
        Total revenue reached ${data.get('revenue', {}).get('total_revenue', 0):,}.
        """
    
    async def _format_chart_data(self, data: Dict, chart_type: str) -> List[Dict]:
        """Format data for charts"""
        # Mock implementation
        if chart_type == "trend":
            return [
                {"date": "2024-01-01", "count": 100},
                {"date": "2024-01-02", "count": 105},
                {"date": "2024-01-03", "count": 110}
            ]
        elif chart_type == "by_service":
            return [
                {"service": "Consulting", "revenue": 50000},
                {"service": "Implementation", "revenue": 40000},
                {"service": "Support", "revenue": 35000}
            ]
        elif chart_type == "by_source":
            return [
                {"source": "Website", "value": 60},
                {"source": "Referral", "value": 40},
                {"source": "Cold Outreach", "value": 30},
                {"source": "Social", "value": 20}
            ]
        
        return []
    
    async def _get_recent_activities(self) -> List[Dict]:
        """Get recent activities for table"""
        return [
            {"date": "2024-01-21", "activity": "New Prospect", "prospect": "ABC Corp", "status": "New"},
            {"date": "2024-01-21", "activity": "Meeting Scheduled", "prospect": "XYZ Inc", "status": "Qualified"},
            {"date": "2024-01-20", "activity": "Deal Closed", "prospect": "123 LLC", "status": "Converted"}
        ]
    
    async def _generate_pdf_report(self, report: Dict) -> str:
        """Generate PDF version of report"""
        # Mock PDF generation
        return f"/reports/pdf/{report['id']}.pdf"
    
    async def _generate_excel_report(self, report: Dict) -> str:
        """Generate Excel version of report"""
        # Mock Excel generation
        return f"/reports/excel/{report['id']}.xlsx"
    
    async def _send_report_notification(self, report: Dict):
        """Send report notification"""
        notification = {
            "type": "report_generated",
            "report_id": report["id"],
            "report_type": report["type"],
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("notifications", notification)
    
    async def _get_active_prospects_count(self) -> int:
        """Get current active prospects count"""
        # Mock real-time data
        return 150
    
    async def _get_current_conversion_rate(self) -> float:
        """Get current conversion rate"""
        return 0.167
    
    async def _get_today_outreach_count(self) -> int:
        """Get today's outreach count"""
        return 25
    
    async def _get_today_meetings(self) -> int:
        """Get today's meetings count"""
        return 5
    
    async def _get_today_revenue(self) -> float:
        """Get today's revenue"""
        return 2500.0
    
    def _calculate_next_run(self, frequency: str) -> str:
        """Calculate next run time for scheduled reports"""
        if frequency == "daily":
            next_run = datetime.now() + timedelta(days=1)
        elif frequency == "weekly":
            next_run = datetime.now() + timedelta(weeks=1)
        elif frequency == "monthly":
            next_run = datetime.now() + timedelta(days=30)
        else:
            next_run = datetime.now() + timedelta(weeks=1)
        
        return next_run.isoformat()
    
    async def _setup_scheduled_task(self, schedule: Dict):
        """Set up scheduled report generation"""
        # Mock scheduler setup
        pass

# Create the reporting engine agent
def create_reporting_engine_agent() -> DeepAgent:
    """Create and configure the reporting engine agent"""
    
    agent = create_deep_agent(
        name="reporting_engine",
        model="openai:gpt-4-turbo-preview",
        system_prompt="""You are a Reporting Engine Agent responsible for:
        1. Generating dynamic dashboards using AG-UI protocol
        2. Creating detailed reports in various formats
        3. Providing real-time metrics for live monitoring
        4. Scheduling recurring report generation
        5. Analyzing data and generating insights
        
        Always ensure data accuracy and provide clear, actionable insights.""",
        tools=[
            {
                "name": "generate_dashboard",
                "description": "Generate dynamic dashboard",
                "parameters": {
                    "dashboard_config": "object"
                }
            },
            {
                "name": "generate_report",
                "description": "Generate detailed report",
                "parameters": {
                    "report_config": "object"
                }
            },
            {
                "name": "get_real_time_metrics",
                "description": "Get real-time metrics",
                "parameters": {
                    "metrics_request": "object"
                }
            },
            {
                "name": "schedule_report",
                "description": "Schedule recurring report",
                "parameters": {
                    "schedule_config": "object"
                }
            }
        ]
    )
    
    # Initialize the agent with our handler
    handler = ReportingEngineAgent()
    
    # Register tool handlers
    async def generate_dashboard_tool(dashboard_config: Dict[str, Any]):
        return await handler.generate_dashboard(dashboard_config)
    
    async def generate_report_tool(report_config: Dict[str, Any]):
        return await handler.generate_report(report_config)
    
    async def get_real_time_metrics_tool(metrics_request: Dict[str, Any]):
        return await handler.get_real_time_metrics(metrics_request)
    
    async def schedule_report_tool(schedule_config: Dict[str, Any]):
        return await handler.schedule_report(schedule_config)
    
    agent.register_tool("generate_dashboard", generate_dashboard_tool)
    agent.register_tool("generate_report", generate_report_tool)
    agent.register_tool("get_real_time_metrics", get_real_time_metrics_tool)
    agent.register_tool("schedule_report", schedule_report_tool)
    
    return agent

# Export the agent creation function
__all__ = ["create_reporting_engine_agent", "ReportingEngineAgent"]
