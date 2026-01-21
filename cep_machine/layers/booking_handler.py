"""
CEP Layer 4: Booking Handler

Handle Calendly webhooks and update CRM with meeting data.
Creates calendar invites and manages booking lifecycle.

Container Alignment: Sales
Φ Contribution: +0.07

Input: Calendly webhook events
Output: CRM updates + calendar invites
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import parse_qs


class BookingStatus(Enum):
    """Status of booking events."""
    INVITEE_CREATED = "invitee.created"
    INVITEE_CANCELED = "invitee.canceled"
    INVITEE_RESCHEDULED = "invitee.rescheduled"


class MeetingType(Enum):
    """Types of meetings."""
    DISCOVERY = "discovery"
    DEMO = "demo"
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"


@dataclass
class Meeting:
    """A scheduled meeting."""
    id: str
    calendly_event_id: str
    calendly_invitee_id: str
    prospect_id: str
    business_name: str
    contact_email: str
    contact_phone: Optional[str]
    meeting_type: MeetingType
    scheduled_start: datetime
    scheduled_end: datetime
    timezone: str
    location: str
    status: BookingStatus
    questions_answers: Dict[str, str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    calendar_event_id: Optional[str] = None
    zoom_link: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "calendly_event_id": self.calendly_event_id,
            "calendly_invitee_id": self.calendly_invitee_id,
            "prospect_id": self.prospect_id,
            "business_name": self.business_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "meeting_type": self.meeting_type.value,
            "scheduled_start": self.scheduled_start.isoformat(),
            "scheduled_end": self.scheduled_end.isoformat(),
            "timezone": self.timezone,
            "location": self.location,
            "status": self.status.value,
            "questions_answers": self.questions_answers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "calendar_event_id": self.calendar_event_id,
            "zoom_link": self.zoom_link,
            "metadata": self.metadata,
        }


@dataclass
class BookingResult:
    """Result of booking processing."""
    webhook_processed: bool
    meeting_created: bool
    calendar_invite_sent: bool
    zoom_meeting_created: bool
    crm_updated: bool
    meeting: Optional[Meeting] = None
    errors: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_processed": self.webhook_processed,
            "meeting_created": self.meeting_created,
            "calendar_invite_sent": self.calendar_invite_sent,
            "zoom_meeting_created": self.zoom_meeting_created,
            "crm_updated": self.crm_updated,
            "meeting": self.meeting.to_dict() if self.meeting else None,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class BookingHandler:
    """
    Layer 4: Booking Handler
    
    Processes Calendly webhooks and manages meeting lifecycle.
    Creates calendar invites and updates CRM.
    """
    
    def __init__(
        self,
        calendly_signing_key: Optional[str] = None,
        dry_run: bool = True,
    ):
        self.calendly_signing_key = calendly_signing_key
        self.dry_run = dry_run
        self.meetings: Dict[str, Meeting] = {}  # In-memory storage
    
    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> BookingResult:
        """
        Handle incoming Calendly webhook.
        
        Args:
            payload: Webhook payload from Calendly
            signature: X-Calendly-Signature header
            timestamp: X-Calendly-Timestamp header
        
        Returns:
            BookingResult with processing details
        """
        start_time = datetime.now()
        
        print(f"[Layer 4] Processing webhook: {payload.get('event', {}).get('action')}")
        
        result = BookingResult(
            webhook_processed=False,
            meeting_created=False,
            calendar_invite_sent=False,
            zoom_meeting_created=False,
            crm_updated=False,
        )
        
        try:
            # Verify webhook signature if key provided
            if self.calendly_signing_key and signature and timestamp:
                if not self._verify_signature(payload, signature, timestamp):
                    result.errors.append("Invalid webhook signature")
                    return result
            
            # Extract event data
            event = payload.get("event", {})
            action = event.get("action")
            
            if action == BookingStatus.INVITEE_CREATED.value:
                meeting = await self._process_invitee_created(event)
                if meeting:
                    result.meeting = meeting
                    result.meeting_created = True
                    
                    # Create calendar invite
                    calendar_sent = await self._create_calendar_invite(meeting)
                    result.calendar_invite_sent = calendar_sent
                    
                    # Create Zoom meeting
                    zoom_created = await self._create_zoom_meeting(meeting)
                    result.zoom_meeting_created = zoom_created
                    
                    # Update CRM
                    crm_updated = await self._update_crm(meeting)
                    result.crm_updated = crm_updated
            
            elif action == BookingStatus.INVITEE_CANCELED.value:
                await self._process_invitee_canceled(event)
            
            elif action == BookingStatus.INVITEE_RESCHEDULED.value:
                await self._process_invitee_rescheduled(event)
            
            result.webhook_processed = True
            
        except Exception as e:
            result.errors.append(f"Processing error: {str(e)}")
            print(f"[Layer 4] Error: {e}")
        
        result.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"[Layer 4] Webhook processed in {result.processing_time_ms}ms")
        
        return result
    
    def _verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: str,
    ) -> bool:
        """Verify Calendly webhook signature."""
        if not self.calendly_signing_key:
            return True  # Skip verification if no key
        
        # Create the signed payload
        payload_str = json.dumps(payload, separators=(",", ":"))
        signed_payload = f"{timestamp}.{payload_str}"
        
        # Generate expected signature
        expected = hmac.new(
            self.calendly_signing_key.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected, signature)
    
    async def _process_invitee_created(self, event: Dict[str, Any]) -> Optional[Meeting]:
        """Process new booking creation."""
        payload = event.get("payload", {})
        
        # Extract invitee data
        invitee = payload.get("invitee", {})
        event_data = payload.get("event", {})
        
        # Extract meeting details
        calendly_event_id = event_data.get("uuid")
        calendly_invitee_id = invitee.get("uuid")
        
        # Extract contact info
        email = invitee.get("email")
        phone = invitee.get("phone")
        name = invitee.get("name", "")
        
        # Extract time
        start_time = datetime.fromisoformat(event_data.get("start_time").replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(event_data.get("end_time").replace("Z", "+00:00"))
        
        # Extract location
        location = event_data.get("location", {}).get("join_url", "Phone call")
        
        # Extract questions and answers
        questions_answers = {}
        for qa in invitee.get("questions_and_answers", []):
            questions_answers[qa.get("question", "")] = qa.get("answer", "")
        
        # Determine meeting type from questions or event type
        meeting_type = self._determine_meeting_type(questions_answers, event_data)
        
        # Create meeting
        meeting = Meeting(
            id=f"meeting_{calendly_invitee_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            calendly_event_id=calendly_event_id,
            calendly_invitee_id=calendly_invitee_id,
            prospect_id=self._extract_prospect_id(questions_answers),
            business_name=self._extract_business_name(questions_answers, name),
            contact_email=email,
            contact_phone=phone,
            meeting_type=meeting_type,
            scheduled_start=start_time,
            scheduled_end=end_time,
            timezone=event_data.get("timezone", "UTC"),
            location=location,
            status=BookingStatus.INVITEE_CREATED,
            questions_answers=questions_answers,
            metadata={
                "calendly_event_type": event_data.get("event_type", {}).get("name"),
                "cancelled": False,
            },
        )
        
        # Store meeting
        self.meetings[meeting.id] = meeting
        
        print(f"[Layer 4] ✓ Meeting created: {meeting.business_name}")
        
        return meeting
    
    async def _process_invitee_canceled(self, event: Dict[str, Any]) -> None:
        """Process booking cancellation."""
        payload = event.get("payload", {})
        invitee = payload.get("invitee", {})
        calendly_invitee_id = invitee.get("uuid")
        
        # Find and update meeting
        for meeting in self.meetings.values():
            if meeting.calendly_invitee_id == calendly_invitee_id:
                meeting.status = BookingStatus.INVITEE_CANCELED
                meeting.updated_at = datetime.now()
                meeting.metadata["cancelled"] = True
                
                # Cancel calendar event
                await self._cancel_calendar_event(meeting)
                
                print(f"[Layer 4] ✓ Meeting cancelled: {meeting.business_name}")
                break
    
    async def _process_invitee_rescheduled(self, event: Dict[str, Any]) -> None:
        """Process booking reschedule."""
        payload = event.get("payload", {})
        invitee = payload.get("invitee", {})
        new_event = payload.get("new_event", {})
        calendly_invitee_id = invitee.get("uuid")
        
        # Find and update meeting
        for meeting in self.meetings.values():
            if meeting.calendly_invitee_id == calendly_invitee_id:
                # Update time
                meeting.scheduled_start = datetime.fromisoformat(
                    new_event.get("start_time").replace("Z", "+00:00")
                )
                meeting.scheduled_end = datetime.fromisoformat(
                    new_event.get("end_time").replace("Z", "+00:00")
                )
                meeting.status = BookingStatus.INVITEE_RESCHEDULED
                meeting.updated_at = datetime.now()
                
                # Update calendar event
                await self._update_calendar_event(meeting)
                
                print(f"[Layer 4] ✓ Meeting rescheduled: {meeting.business_name}")
                break
    
    def _determine_meeting_type(
        self,
        questions_answers: Dict[str, str],
        event_data: Dict[str, Any],
    ) -> MeetingType:
        """Determine meeting type from data."""
        # Check questions first
        for question, answer in questions_answers.items():
            answer_lower = answer.lower()
            if "demo" in answer_lower:
                return MeetingType.DEMO
            elif "consultation" in answer_lower:
                return MeetingType.CONSULTATION
            elif "follow" in answer_lower:
                return MeetingType.FOLLOW_UP
        
        # Check event type name
        event_type_name = event_data.get("event_type", {}).get("name", "").lower()
        if "demo" in event_type_name:
            return MeetingType.DEMO
        elif "consultation" in event_type_name:
            return MeetingType.CONSULTATION
        
        # Default to discovery
        return MeetingType.DISCOVERY
    
    def _extract_prospect_id(self, questions_answers: Dict[str, str]) -> str:
        """Extract prospect ID from questions."""
        for question, answer in questions_answers.items():
            if "prospect" in question.lower() and answer:
                return answer
        return "unknown_prospect"
    
    def _extract_business_name(
        self,
        questions_answers: Dict[str, str],
        fallback_name: str,
    ) -> str:
        """Extract business name from questions."""
        for question, answer in questions_answers.items():
            if "business" in question.lower() and answer:
                return answer
        return fallback_name
    
    async def _create_calendar_invite(self, meeting: Meeting) -> bool:
        """Create calendar invite for meeting."""
        if self.dry_run:
            print(f"[Layer 4] (DRY RUN) Would create calendar invite for {meeting.business_name}")
            return True
        
        # In production, use Google Calendar API, Outlook API, etc.
        try:
            # Simulate calendar creation
            meeting.calendar_event_id = f"cal_{meeting.id}"
            print(f"[Layer 4] ✓ Calendar invite created: {meeting.calendar_event_id}")
            return True
        except Exception as e:
            print(f"[Layer 4] Calendar creation failed: {e}")
            return False
    
    async def _create_zoom_meeting(self, meeting: Meeting) -> bool:
        """Create Zoom meeting for virtual meetings."""
        if "phone" in meeting.location.lower():
            return False  # Phone call, no Zoom needed
        
        if self.dry_run:
            print(f"[Layer 4] (DRY RUN) Would create Zoom meeting for {meeting.business_name}")
            meeting.zoom_link = f"https://zoom.us/j/dummy-{meeting.id}"
            return True
        
        # In production, use Zoom API
        try:
            # Simulate Zoom creation
            meeting.zoom_link = f"https://zoom.us/j/{meeting.id[:10]}"
            print(f"[Layer 4] ✓ Zoom meeting created: {meeting.zoom_link}")
            return True
        except Exception as e:
            print(f"[Layer 4] Zoom creation failed: {e}")
            return False
    
    async def _update_crm(self, meeting: Meeting) -> bool:
        """Update CRM with meeting data."""
        if self.dry_run:
            print(f"[Layer 4] (DRY RUN) Would update CRM for {meeting.business_name}")
            return True
        
        # In production, update your CRM (HubSpot, Salesforce, etc.)
        try:
            # Simulate CRM update
            print(f"[Layer 4] ✓ CRM updated for {meeting.business_name}")
            return True
        except Exception as e:
            print(f"[Layer 4] CRM update failed: {e}")
            return False
    
    async def _cancel_calendar_event(self, meeting: Meeting) -> bool:
        """Cancel calendar event."""
        if self.dry_run:
            print(f"[Layer 4] (DRY RUN) Would cancel calendar event for {meeting.business_name}")
            return True
        
        # In production, call calendar API
        return True
    
    async def _update_calendar_event(self, meeting: Meeting) -> bool:
        """Update calendar event after reschedule."""
        if self.dry_run:
            print(f"[Layer 4] (DRY RUN) Would update calendar event for {meeting.business_name}")
            return True
        
        # In production, call calendar API
        return True
    
    async def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID."""
        return self.meetings.get(meeting_id)
    
    async def get_meetings_by_prospect(self, prospect_id: str) -> List[Meeting]:
        """Get all meetings for a prospect."""
        return [m for m in self.meetings.values() if m.prospect_id == prospect_id]
    
    async def get_upcoming_meetings(self, hours: int = 24) -> List[Meeting]:
        """Get upcoming meetings within specified hours."""
        cutoff = datetime.now() + timedelta(hours=hours)
        return [
            m for m in self.meetings.values()
            if m.scheduled_start <= cutoff
            and m.status != BookingStatus.INVITEE_CANCELED
        ]


# Layer 4 Entry Point
async def run_layer(
    webhook_payload: Dict[str, Any],
    signature: Optional[str] = None,
    timestamp: Optional[str] = None,
    dry_run: bool = True,
) -> BookingResult:
    """
    Main entry point for Layer 4: Booking Handler
    
    Args:
        webhook_payload: Calendly webhook payload
        signature: X-Calendly-Signature header
        timestamp: X-Calendly-Timestamp header
        dry_run: If True, simulate external API calls
    
    Returns:
        BookingResult with processing details
    """
    print(f"\n{'='*60}")
    print(f"[Layer 4] BOOKING HANDLER")
    print(f"Event: {webhook_payload.get('event', {}).get('action')}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    handler = BookingHandler(dry_run=dry_run)
    result = await handler.handle_webhook(webhook_payload, signature, timestamp)
    
    print(f"\n[Layer 4] ✓ Complete")
    print(f"  - Webhook processed: {result.webhook_processed}")
    print(f"  - Meeting created: {result.meeting_created}")
    print(f"  - Calendar invite: {result.calendar_invite_sent}")
    print(f"  - Zoom meeting: {result.zoom_meeting_created}")
    print(f"  - CRM updated: {result.crm_updated}")
    print(f"  - Processing time: {result.processing_time_ms}ms")
    
    return result


# Export
__all__ = [
    "Meeting",
    "BookingResult",
    "BookingHandler",
    "BookingStatus",
    "MeetingType",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Sample webhook payload
    sample_webhook = {
        "event": {
            "action": "invitee.created",
            "created_at": "2024-01-20T12:00:00Z",
            "payload": {
                "event": {
                    "uuid": "event_123",
                    "start_time": "2024-01-21T14:00:00Z",
                    "end_time": "2024-01-21T14:30:00Z",
                    "timezone": "America/New_York",
                    "location": {"join_url": "https://zoom.us/j/123456"},
                    "event_type": {"name": "Discovery Call"},
                },
                "invitee": {
                    "uuid": "invitee_123",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "questions_and_answers": [
                        {"question": "Business Name", "answer": "Test Dental Clinic"},
                        {"question": "What would you like to discuss?", "answer": "GBP optimization demo"},
                    ],
                },
            },
        },
    }
    
    dry_run = "--live" not in sys.argv
    result = asyncio.run(run_layer(sample_webhook, dry_run=dry_run))
    
    print("\n" + "="*60)
    print("BOOKING RESULT:")
    print("="*60)
    
    if result.meeting:
        print(f"\nMeeting ID: {result.meeting.id}")
        print(f"Business: {result.meeting.business_name}")
        print(f"Type: {result.meeting.meeting_type.value}")
        print(f"Time: {result.meeting.scheduled_start} - {result.meeting.scheduled_end}")
        print(f"Location: {result.meeting.location}")
        if result.meeting.zoom_link:
            print(f"Zoom: {result.meeting.zoom_link}")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
