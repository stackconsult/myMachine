"""
Tests for Layer 4: Booking Handler

Success Criteria: Webhook listener processes bookings and updates CRM.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.booking_handler import (
    Meeting,
    BookingResult,
    BookingHandler,
    BookingStatus,
    MeetingType,
    run_layer,
)


class TestMeeting:
    """Test Meeting data class."""
    
    def test_meeting_creation(self):
        """Test creating a meeting."""
        start = datetime.now()
        end = start + timedelta(hours=1)
        
        meeting = Meeting(
            id="meeting_001",
            calendly_event_id="event_123",
            calendly_invitee_id="invitee_123",
            prospect_id="prospect_001",
            business_name="Test Dental",
            contact_email="test@example.com",
            meeting_type=MeetingType.DISCOVERY,
            scheduled_start=start,
            scheduled_end=end,
            timezone="America/New_York",
            location="Zoom",
            status=BookingStatus.INVITEE_CREATED,
            questions_answers={},
        )
        
        assert meeting.id == "meeting_001"
        assert meeting.business_name == "Test Dental"
        assert meeting.meeting_type == MeetingType.DISCOVERY
        assert meeting.status == BookingStatus.INVITEE_CREATED
    
    def test_meeting_to_dict(self):
        """Test meeting serialization."""
        start = datetime.now()
        end = start + timedelta(hours=1)
        
        meeting = Meeting(
            id="meeting_001",
            calendly_event_id="event_123",
            calendly_invitee_id="invitee_123",
            prospect_id="prospect_001",
            business_name="Test Dental",
            contact_email="test@example.com",
            meeting_type=MeetingType.DISCOVERY,
            scheduled_start=start,
            scheduled_end=end,
            timezone="America/New_York",
            location="Zoom",
            status=BookingStatus.INVITEE_CREATED,
            questions_answers={},
        )
        
        data = meeting.to_dict()
        assert data["id"] == "meeting_001"
        assert data["business_name"] == "Test Dental"
        assert data["meeting_type"] == "discovery"
        assert data["status"] == "invitee.created"


class TestBookingHandler:
    """Test BookingHandler functionality."""
    
    @pytest.fixture
    def handler(self):
        return BookingHandler(dry_run=True)
    
    @pytest.fixture
    def sample_webhook(self):
        return {
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
    
    @pytest.mark.asyncio
    async def test_handle_webhook_invitee_created(self, handler, sample_webhook):
        """Test handling invitee.created webhook."""
        result = await handler.handle_webhook(sample_webhook)
        
        assert result.webhook_processed
        assert result.meeting_created
        assert result.calendar_invite_sent
        assert result.zoom_meeting_created
        assert result.crm_updated
        assert result.meeting is not None
        assert result.meeting.business_name == "Test Dental Clinic"
    
    @pytest.mark.asyncio
    async def test_handle_webhook_canceled(self, handler, sample_webhook):
        """Test handling invitee.canceled webhook."""
        # First create a meeting
        await handler.handle_webhook(sample_webhook)
        
        # Then cancel it
        cancel_webhook = {
            "event": {
                "action": "invitee.canceled",
                "payload": {
                    "invitee": {
                        "uuid": "invitee_123",
                    },
                },
            },
        }
        
        result = await handler.handle_webhook(cancel_webhook)
        
        assert result.webhook_processed
        
        # Check meeting was cancelled
        for meeting in handler.meetings.values():
            if meeting.calendly_invitee_id == "invitee_123":
                assert meeting.status == BookingStatus.INVITEE_CANCELED
                assert meeting.metadata["cancelled"] is True
    
    @pytest.mark.asyncio
    async def test_handle_webhook_rescheduled(self, handler, sample_webhook):
        """Test handling invitee.rescheduled webhook."""
        # First create a meeting
        await handler.handle_webhook(sample_webhook)
        
        # Then reschedule it
        reschedule_webhook = {
            "event": {
                "action": "invitee.rescheduled",
                "payload": {
                    "invitee": {
                        "uuid": "invitee_123",
                    },
                    "new_event": {
                        "start_time": "2024-01-21T15:00:00Z",
                        "end_time": "2024-01-21T15:30:00Z",
                    },
                },
            },
        }
        
        result = await handler.handle_webhook(reschedule_webhook)
        
        assert result.webhook_processed
        
        # Check meeting was rescheduled
        for meeting in handler.meetings.values():
            if meeting.calendly_invitee_id == "invitee_123":
                assert meeting.status == BookingStatus.INVITEE_RESCHEDULED
                assert "15:00" in meeting.scheduled_start.isoformat()
    
    def test_determine_meeting_type(self, handler):
        """Test meeting type determination."""
        # Demo from questions
        questions = {"What would you like to discuss?": "I want a demo"}
        event_data = {}
        meeting_type = handler._determine_meeting_type(questions, event_data)
        assert meeting_type == MeetingType.DEMO
        
        # Consultation from event type
        questions = {}
        event_data = {"event_type": {"name": "Free Consultation"}}
        meeting_type = handler._determine_meeting_type(questions, event_data)
        assert meeting_type == MeetingType.CONSULTATION
        
        # Default to discovery
        meeting_type = handler._determine_meeting_type({}, {})
        assert meeting_type == MeetingType.DISCOVERY
    
    def test_extract_prospect_id(self, handler):
        """Test prospect ID extraction."""
        questions = {"Prospect ID": "prospect_123"}
        prospect_id = handler._extract_prospect_id(questions)
        assert prospect_id == "prospect_123"
        
        # No prospect ID
        prospect_id = handler._extract_prospect_id({})
        assert prospect_id == "unknown_prospect"
    
    def test_extract_business_name(self, handler):
        """Test business name extraction."""
        questions = {"Business Name": "Test Business"}
        name = handler._extract_business_name(questions, "Fallback Name")
        assert name == "Test Business"
        
        # Fallback to provided name
        name = handler._extract_business_name({}, "Fallback Name")
        assert name == "Fallback Name"
    
    @pytest.mark.asyncio
    async def test_get_meeting(self, handler, sample_webhook):
        """Test retrieving a meeting."""
        # Create a meeting
        await handler.handle_webhook(sample_webhook)
        
        # Get the meeting
        meetings = list(handler.meetings.values())
        if meetings:
            meeting = await handler.get_meeting(meetings[0].id)
            assert meeting is not None
            assert meeting.business_name == "Test Dental Clinic"
    
    @pytest.mark.asyncio
    async def test_get_meetings_by_prospect(self, handler, sample_webhook):
        """Test getting meetings by prospect."""
        # Create a meeting
        await handler.handle_webhook(sample_webhook)
        
        # Get meetings for prospect
        meetings = await handler.get_meetings_by_prospect("unknown_prospect")
        assert len(meetings) >= 1
    
    @pytest.mark.asyncio
    async def test_get_upcoming_meetings(self, handler, sample_webhook):
        """Test getting upcoming meetings."""
        # Create a meeting with future time
        future_webhook = {
            "event": {
                "action": "invitee.created",
                "payload": {
                    "event": {
                        "uuid": "event_future",
                        "start_time": (datetime.now() + timedelta(hours=12)).isoformat() + "Z",
                        "end_time": (datetime.now() + timedelta(hours=13)).isoformat() + "Z",
                        "timezone": "America/New_York",
                        "location": {"join_url": "https://zoom.us/j/123456"},
                    },
                    "invitee": {
                        "uuid": "invitee_future",
                        "name": "Future User",
                        "email": "future@example.com",
                        "questions_and_answers": [],
                    },
                },
            },
        }
        
        await handler.handle_webhook(future_webhook)
        
        # Get upcoming meetings
        upcoming = await handler.get_upcoming_meetings(hours=24)
        assert len(upcoming) >= 1


class TestLayerEntry:
    """Test Layer 4 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        webhook = {
            "event": {
                "action": "invitee.created",
                "payload": {
                    "event": {
                        "uuid": "event_123",
                        "start_time": "2024-01-21T14:00:00Z",
                        "end_time": "2024-01-21T14:30:00Z",
                        "timezone": "America/New_York",
                        "location": {"join_url": "https://zoom.us/j/123456"},
                    },
                    "invitee": {
                        "uuid": "invitee_123",
                        "name": "Test User",
                        "email": "test@example.com",
                        "questions_and_answers": [],
                    },
                },
            },
        }
        
        result = await run_layer(webhook, dry_run=True)
        
        assert isinstance(result, BookingResult)
        assert result.webhook_processed
        assert result.meeting_created
        assert result.calendar_invite_sent
        assert result.zoom_meeting_created
        assert result.crm_updated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
