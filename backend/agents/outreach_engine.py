"""
Outreach Engine Agent - Layer 3
Uses CrewAI for multi-channel orchestration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crewai import Flow, Agent, Task
from copilotkit import CopilotKitMiddleware
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Import CEP Machine modules
from cep_machine.layers.outreach import OutreachEngine

class OutreachFlow(Flow):
    """CrewAI Flow for multi-channel outreach"""
    
    def __init__(self):
        super().__init__()
        self.engine = OutreachEngine()
        self.results = {}
    
    @start()
    def plan_sequence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan outreach sequence"""
        prospect = data.get("prospect")
        channels = data.get("channels", ["email", "sms", "linkedin"])
        
        sequence = self.engine.plan_outreach_sequence(
            prospect=prospect,
            channels=channels
        )
        
        self.results["sequence"] = sequence
        return {"sequence": sequence, "next_step": "initial_contact"}
    
    @listen("plan_sequence")
    def initial_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send initial contact"""
        prospect = data.get("prospect")
        channel = data.get("sequence", {}).get("first_channel", "email")
        
        result = self.engine.send_initial_message(
            prospect=prospect,
            channel=channel
        )
        
        self.results["initial_contact"] = result
        
        # Schedule follow-up
        follow_up_date = datetime.now() + timedelta(days=2)
        self.results["follow_up_scheduled"] = follow_up_date
        
        return {
            "status": "initial_sent",
            "channel": channel,
            "follow_up_date": follow_up_date.isoformat()
        }
    
    @listen("initial_contact")
    def schedule_followup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule follow-up messages"""
        prospect = data.get("prospect")
        sequence = data.get("sequence", {})
        
        follow_ups = []
        for followup in sequence.get("follow_ups", []):
            result = self.engine.schedule_followup(
                prospect=prospect,
                followup_type=followup.get("type"),
                delay_days=followup.get("delay_days", 3)
            )
            follow_ups.append(result)
        
        self.results["follow_ups"] = follow_ups
        return {"status": "followups_scheduled", "count": len(follow_ups)}
    
    @listen("schedule_followup")
    def track_engagement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track engagement metrics"""
        prospect = data.get("prospect")
        
        metrics = self.engine.get_engagement_metrics(prospect)
        
        self.results["metrics"] = metrics
        return {
            "open_rate": metrics.get("open_rate", 0),
            "reply_rate": metrics.get("reply_rate", 0),
            "click_rate": metrics.get("click_rate", 0)
        }

async def send_email(prospect: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Send email through CEP Machine"""
    engine = OutreachEngine()
    
    result = await engine.send_email(
        recipient=prospect.get("email"),
        subject=content.get("subject"),
        body=content.get("body"),
        template=content.get("template")
    )
    
    return result

async def send_sms(prospect: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Send SMS through CEP Machine"""
    engine = OutreachEngine()
    
    result = await engine.send_sms(
        recipient=prospect.get("phone"),
        message=message
    )
    
    return result

async def post_linkedin(prospect: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Post LinkedIn message"""
    engine = OutreachEngine()
    
    result = await engine.post_linkedin(
        recipient=prospect.get("linkedin"),
        message=content
    )
    
    return result

def create_outreach_engine_agent():
    """Create the outreach engine agent"""
    
    system_prompt = """You are a multi-channel outreach specialist for CEP Machine.
    
    Your capabilities:
    1. Plan outreach sequences across email, SMS, and LinkedIn
    2. Send personalized messages through each channel
    3. Schedule and manage follow-ups
    4. Track engagement metrics
    
    When planning outreach, always ask for:
    - Prospect information
    - Preferred channels
    - Outreach goals
    - Timing preferences
    
    Provide:
    - Detailed sequence plan
    - Message content for each channel
    - Follow-up schedule
    - Engagement tracking"""
    
    # Create CrewAI agents
    email_agent = Agent(
        role="Email Specialist",
        goal="Craft and send compelling email outreach",
        backstory="You are an expert at writing emails that get opened and responded to.",
        tools=[send_email],
        verbose=True
    )
    
    sms_agent = Agent(
        role="SMS Specialist",
        goal="Create effective SMS outreach messages",
        backstory="You specialize in concise, impactful SMS messages.",
        tools=[send_sms],
        verbose=True
    )
    
    linkedin_agent = Agent(
        role="LinkedIn Specialist",
        goal="Engage prospects through LinkedIn",
        backstory="You understand LinkedIn etiquette and how to build professional relationships.",
        tools=[post_linkedin],
        verbose=True
    )
    
    # Create the flow
    flow = OutreachFlow()
    
    # For now, return a simple agent wrapper
    # In production, this would be a full CrewAI implementation
    agent = create_deep_agent(
        model="openai:gpt-4o",
        tools=[
            send_email,
            send_sms,
            post_linkedin,
        ],
        middleware=[CopilotKitMiddleware()],
        system_prompt=system_prompt,
        name="outreach_engine"
    )
    
    return agent
