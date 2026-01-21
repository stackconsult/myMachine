from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
import os
from typing import Dict, Any

# CEP Machine Tools
def search_prospects(location: str, category: str) -> str:
    """Search for businesses in a location by category"""
    return f"Found 15 prospects in {location} for {category}: ABC Corp, XYZ LLC, Business Inc..."

def generate_pitch(business_name: str, industry: str) -> str:
    """Generate personalized pitch for a business"""
    return f"Personalized pitch for {business_name} in {industry}: Subject: Transforming Your {industry} Business..."

def send_outreach(contact_email: str, message: str, channel: str) -> str:
    """Send outreach message via specified channel"""
    return f"Message sent to {contact_email} via {channel}: Message delivered successfully"

def optimize_gbp(business_id: str, updates: Dict[str, Any]) -> str:
    """Optimize Google Business Profile"""
    return f"GBP optimized for {business_id}: Updated business hours, photos, and description"

def generate_report(date_range: str, metrics: list) -> str:
    """Generate performance report"""
    return f"Report for {date_range}: Revenue up 15%, leads increased 23%, customer satisfaction 4.8/5"

def track_finances(transaction_type: str, amount: float, category: str) -> str:
    """Track financial transactions"""
    return f"Recorded {transaction_type}: ${amount} in {category} category"

def analyze_performance(layer_name: str, time_period: str) -> str:
    """Analyze performance of a specific layer"""
    return f"Analysis for {layer_name} ({time_period}): Efficiency improved by 18%, ROI increased 22%"

# Create the CEP Machine Deep Agent
cep_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[
        search_prospects,
        generate_pitch, 
        send_outreach,
        optimize_gbp,
        generate_report,
        track_finances,
        analyze_performance
    ],
    middleware=[CopilotKitMiddleware()], # for frontend tools and context
    system_prompt="""You are a CEP Machine assistant - a 9-layer AI agent framework for business automation.

You have access to tools for:
- search_prospects: Find businesses by location/category
- generate_pitch: Create personalized outreach content
- send_outreach: Send messages via email/social media
- optimize_gbp: Optimize Google Business Profiles
- generate_report: Create performance reports
- track_finances: Track revenue and expenses
- analyze_performance: Analyze layer performance

Guide users through business automation workflows using these tools."""
)
