"""
Booking Handler Agent - Layer 4
Handles meeting scheduling, calendar integration, and human-in-the-loop approvals
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import json
import os

# CopilotKit imports
from deepagents import create_deep_agent, DeepAgent
from copilotkit.langchain import copilotkit_emit_state

# CEP Machine imports
from cep_machine.layers.booking_handler import BookingHandler
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class BookingHandlerAgent:
    """Agent for handling booking workflows with HITL"""
    
    def __init__(self):
        self.booking_handler = BookingHandler()
        self.db = get_database()
        self.cache = get_cache()
        
        # Calendar API configurations
        self.google_calendar_config = {
            "enabled": os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true",
            "api_key": os.getenv("GOOGLE_CALENDAR_API_KEY"),
            "calendar_id": os.getenv("GOOGLE_CALENDAR_ID")
        }
        
        self.outlook_config = {
            "enabled": os.getenv("OUTLOOK_CALENDAR_ENABLED", "false").lower() == "true",
            "api_key": os.getenv("OUTLOOK_API_KEY"),
            "calendar_id": os.getenv("OUTLOOK_CALENDAR_ID")
        }
    
    async def check_availability(self, prospect_id: str, preferred_times: List[Dict]) -> Dict[str, Any]:
        """Check calendar availability across configured calendars"""
        available_slots = []
        
        for time_slot in preferred_times:
            # Check Google Calendar
            if self.google_calendar_config["enabled"]:
                google_available = await self._check_google_calendar(time_slot)
                if google_available:
                    available_slots.append({
                        **time_slot,
                        "source": "google_calendar",
                        "confidence": 0.9
                    })
            
            # Check Outlook Calendar
            if self.outlook_config["enabled"]:
                outlook_available = await self._check_outlook_calendar(time_slot)
                if outlook_available:
                    available_slots.append({
                        **time_slot,
                        "source": "outlook_calendar",
                        "confidence": 0.9
                    })
            
            # Check internal availability
            internal_available = await self._check_internal_availability(time_slot)
            if internal_available:
                available_slots.append({
                    **time_slot,
                    "source": "internal",
                    "confidence": 0.8
                })
        
        # Sort by confidence and return top 3 options
        available_slots.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "prospect_id": prospect_id,
            "available_slots": available_slots[:3],
            "requires_approval": True
        }
    
    async def request_approval(self, meeting_details: Dict[str, Any]) -> Dict[str, Any]:
        """Request human approval for meeting scheduling"""
        # Store approval request in database
        approval_request = {
            "id": f"approval_{datetime.now().timestamp()}",
            "prospect_id": meeting_details["prospect_id"],
            "meeting_details": meeting_details,
            "status": "pending_approval",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        await self.db.create("booking_approvals", approval_request)
        
        # Emit state for real-time UI update
        await copilotkit_emit_state(
            {
                "type": "approval_requested",
                "data": approval_request
            },
            {"channel": f"booking_{meeting_details['prospect_id']}"}
        )
        
        return {
            "approval_id": approval_request["id"],
            "status": "pending_approval",
            "message": "Human approval required for meeting scheduling"
        }
    
    async def confirm_meeting(self, approval_id: str, approved: bool, notes: Optional[str] = None) -> Dict[str, Any]:
        """Confirm or reject meeting after human approval"""
        # Get approval request
        approval = await self.db.get("booking_approvals", approval_id)
        
        if not approval:
            return {"error": "Approval request not found"}
        
        if approval["status"] != "pending_approval":
            return {"error": f"Approval already {approval['status']}"}
        
        # Update approval status
        update_data = {
            "status": "approved" if approved else "rejected",
            "reviewed_at": datetime.now().isoformat(),
            "notes": notes
        }
        
        await self.db.update("booking_approvals", approval_id, update_data)
        
        if approved:
            # Create calendar events
            meeting_details = approval["meeting_details"]
            calendar_events = []
            
            # Add to Google Calendar
            if self.google_calendar_config["enabled"]:
                google_event = await self._create_google_calendar_event(meeting_details)
                if google_event:
                    calendar_events.append(google_event)
            
            # Add to Outlook Calendar
            if self.outlook_config["enabled"]:
                outlook_event = await self._create_outlook_event(meeting_details)
                if outlook_event:
                    calendar_events.append(outlook_event)
            
            # Update prospect status
            await self.db.update(
                "prospects",
                meeting_details["prospect_id"],
                {
                    "status": "meeting_scheduled",
                    "meeting_time": meeting_details["time"],
                    "calendar_events": calendar_events,
                    "updated_at": datetime.now().isoformat()
                }
            )
            
            # Send confirmation
            await self._send_meeting_confirmation(meeting_details)
            
            # Emit success state
            await copilotkit_emit_state(
                {
                    "type": "meeting_confirmed",
                    "data": {
                        "prospect_id": meeting_details["prospect_id"],
                        "meeting_time": meeting_details["time"],
                        "calendar_events": calendar_events
                    }
                },
                {"channel": "booking_updates"}
            )
            
            return {
                "status": "meeting_confirmed",
                "calendar_events": calendar_events,
                "prospect_id": meeting_details["prospect_id"]
            }
        else:
            # Handle rejection
            await copilotkit_emit_state(
                {
                    "type": "meeting_rejected",
                    "data": {
                        "approval_id": approval_id,
                        "notes": notes
                    }
                },
                {"channel": "booking_updates"}
            )
            
            return {
                "status": "meeting_rejected",
                "notes": notes
            }
    
    async def _check_google_calendar(self, time_slot: Dict) -> bool:
        """Check Google Calendar availability"""
        # Mock implementation - integrate with Google Calendar API
        # For now, return True if time is during business hours
        hour = datetime.fromisoformat(time_slot["start"]).hour
        return 9 <= hour <= 17
    
    async def _check_outlook_calendar(self, time_slot: Dict) -> bool:
        """Check Outlook Calendar availability"""
        # Mock implementation - integrate with Outlook Calendar API
        hour = datetime.fromisoformat(time_slot["start"]).hour
        return 9 <= hour <= 17
    
    async def _check_internal_availability(self, time_slot: Dict) -> bool:
        """Check internal team availability"""
        # Check against existing meetings in database
        existing = await self.db.list(
            "meetings",
            filters={
                "time": time_slot["start"],
                "status": "confirmed"
            }
        )
        return len(existing) == 0
    
    async def _create_google_calendar_event(self, meeting_details: Dict) -> Optional[Dict]:
        """Create event in Google Calendar"""
        # Mock implementation
        return {
            "platform": "google_calendar",
            "event_id": f"google_{datetime.now().timestamp()}",
            "link": "https://calendar.google.com/event/mock"
        }
    
    async def _create_outlook_event(self, meeting_details: Dict) -> Optional[Dict]:
        """Create event in Outlook Calendar"""
        # Mock implementation
        return {
            "platform": "outlook_calendar",
            "event_id": f"outlook_{datetime.now().timestamp()}",
            "link": "https://outlook.office.com/event/mock"
        }
    
    async def _send_meeting_confirmation(self, meeting_details: Dict):
        """Send meeting confirmation to prospect"""
        # Mock email sending
        confirmation = {
            "prospect_id": meeting_details["prospect_id"],
            "meeting_time": meeting_details["time"],
            "meeting_link": meeting_details.get("meeting_link"),
            "sent_at": datetime.now().isoformat()
        }
        
        await self.db.create("meeting_confirmations", confirmation)

# Create the booking handler agent
def create_booking_handler_agent() -> DeepAgent:
    """Create and configure the booking handler agent"""
    
    agent = create_deep_agent(
        name="booking_handler",
        model="openai:gpt-4-turbo-preview",
        system_prompt="""You are a Booking Handler Agent responsible for:
1. Checking calendar availability across multiple platforms
2. Generating meeting options for prospects
3. Requesting human approval for meeting scheduling
4. Creating calendar events once approved
5. Sending confirmations and tracking RSVPs

Always ensure proper time zone handling and business hour compliance.""",
        tools=[
            {
                "name": "check_availability",
                "description": "Check calendar availability for a prospect",
                "parameters": {
                    "prospect_id": "string",
                    "preferred_times": "array"
                }
            },
            {
                "name": "request_approval",
                "description": "Request human approval for meeting",
                "parameters": {
                    "meeting_details": "object"
                }
            },
            {
                "name": "confirm_meeting",
                "description": "Confirm or reject meeting after approval",
                "parameters": {
                    "approval_id": "string",
                    "approved": "boolean",
                    "notes": "string (optional)"
                }
            }
        ]
    )
    
    # Initialize the agent with our handler
    handler = BookingHandlerAgent()
    
    # Register tool handlers
    async def check_availability_tool(prospect_id: str, preferred_times: List[Dict]):
        return await handler.check_availability(prospect_id, preferred_times)
    
    async def request_approval_tool(meeting_details: Dict[str, Any]):
        return await handler.request_approval(meeting_details)
    
    async def confirm_meeting_tool(approval_id: str, approved: bool, notes: Optional[str] = None):
        return await handler.confirm_meeting(approval_id, approved, notes)
    
    agent.register_tool("check_availability", check_availability_tool)
    agent.register_tool("request_approval", request_approval_tool)
    agent.register_tool("confirm_meeting", confirm_meeting_tool)
    
    return agent

# Export the agent creation function
__all__ = ["create_booking_handler_agent", "BookingHandlerAgent"]
