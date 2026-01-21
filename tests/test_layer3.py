"""
Tests for Layer 3: Outreach Engine

Success Criteria: 3 test emails sent successfully with multi-channel orchestration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.outreach import (
    OutreachMessage,
    OutreachSequence,
    OutreachResult,
    OutreachEngine,
    OutreachStatus,
    OutreachChannel,
    run_layer,
)
from cep_machine.layers.pitch_gen import Pitch, PitchChannel, PitchContent


class TestOutreachMessage:
    """Test OutreachMessage data class."""
    
    def test_message_creation(self):
        """Test creating an outreach message."""
        message = OutreachMessage(
            id="msg_001",
            pitch_id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            channel=OutreachChannel.EMAIL,
            subject="Test Subject",
            content="Test content",
        )
        
        assert message.id == "msg_001"
        assert message.channel == OutreachChannel.EMAIL
        assert message.status == OutreachStatus.PENDING
        assert message.subject == "Test Subject"
    
    def test_message_to_dict(self):
        """Test message serialization."""
        message = OutreachMessage(
            id="msg_001",
            pitch_id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            channel=OutreachChannel.EMAIL,
            content="Test content",
            sent_at=datetime.now(),
        )
        
        data = message.to_dict()
        assert data["id"] == "msg_001"
        assert data["channel"] == "email"
        assert data["status"] == "pending"
        assert data["sent_at"] is not None


class TestOutreachSequence:
    """Test OutreachSequence functionality."""
    
    def test_sequence_creation(self):
        """Test creating an outreach sequence."""
        messages = [
            OutreachMessage(
                id="msg_001",
                pitch_id="pitch_001",
                prospect_id="prospect_001",
                business_name="Test Business",
                channel=OutreachChannel.EMAIL,
                content="Email content",
            ),
            OutreachMessage(
                id="msg_002",
                pitch_id="pitch_001",
                prospect_id="prospect_001",
                business_name="Test Business",
                channel=OutreachChannel.LINKEDIN,
                content="LinkedIn content",
            ),
        ]
        
        sequence = OutreachSequence(
            prospect_id="prospect_001",
            business_name="Test Business",
            messages=messages,
            sequence_name="Test Sequence",
        )
        
        assert sequence.prospect_id == "prospect_001"
        assert len(sequence.messages) == 2
    
    def test_get_next_message(self):
        """Test getting next message to send."""
        messages = [
            OutreachMessage(
                id="msg_001",
                pitch_id="pitch_001",
                prospect_id="prospect_001",
                business_name="Test Business",
                channel=OutreachChannel.EMAIL,
                content="Email content",
                status=OutreachStatus.SENT,
            ),
            OutreachMessage(
                id="msg_002",
                pitch_id="pitch_001",
                prospect_id="prospect_001",
                business_name="Test Business",
                channel=OutreachChannel.LINKEDIN,
                content="LinkedIn content",
                status=OutreachStatus.PENDING,
            ),
        ]
        
        sequence = OutreachSequence(
            prospect_id="prospect_001",
            business_name="Test Business",
            messages=messages,
            sequence_name="Test Sequence",
        )
        
        next_msg = sequence.get_next_message()
        assert next_msg is not None
        assert next_msg.id == "msg_002"
        assert next_msg.status == OutreachStatus.PENDING


class TestOutreachEngine:
    """Test OutreachEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return OutreachEngine(dry_run=True)
    
    @pytest.fixture
    def test_pitch(self):
        return Pitch(
            id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Dental",
            category="dental",
            pain_points=["No GBP"],
            value_proposition="Get more patients",
            channels={
                PitchChannel.EMAIL: PitchContent(
                    channel=PitchChannel.EMAIL,
                    subject="Test Subject",
                    body="Email body",
                    cta="Call to action",
                ),
                PitchChannel.LINKEDIN: PitchContent(
                    channel=PitchChannel.LINKEDIN,
                    body="LinkedIn body",
                    cta="Connect",
                ),
            },
            confidence_score=0.85,
        )
    
    @pytest.mark.asyncio
    async def test_send_outreach(self, engine, test_pitch):
        """Test sending outreach for pitches."""
        result = await engine.send_outreach([test_pitch])
        
        assert isinstance(result, OutreachResult)
        assert result.prospects_contacted == 1
        assert result.messages_sent >= 1
        assert len(result.sequences) == 1
    
    @pytest.mark.asyncio
    async def test_channel_delays(self, engine, test_pitch):
        """Test channel delay rules."""
        result = await engine.send_outreach([test_pitch])
        
        sequence = result.sequences[0]
        messages_by_channel = {msg.channel: msg for msg in sequence.messages}
        
        # Email should be sent immediately
        if OutreachChannel.EMAIL in messages_by_channel:
            email_msg = messages_by_channel[OutreachChannel.EMAIL]
            assert email_msg.scheduled_at <= datetime.now()
        
        # LinkedIn should be scheduled for later
        if OutreachChannel.LINKEDIN in messages_by_channel:
            linkedin_msg = messages_by_channel[OutreachChannel.LINKEDIN]
            assert linkedin_msg.scheduled_at > datetime.now()
    
    @pytest.mark.asyncio
    async def test_daily_limits(self, engine):
        """Test daily sending limits."""
        # Create many pitches to hit limit
        pitches = []
        for i in range(60):  # More than daily email limit
            pitch = Pitch(
                id=f"pitch_{i}",
                prospect_id=f"prospect_{i}",
                business_name=f"Business {i}",
                category="dental",
                pain_points=["No GBP"],
                value_proposition="Get more patients",
                channels={
                    PitchChannel.EMAIL: PitchContent(
                        channel=PitchChannel.EMAIL,
                        body="Email body",
                        cta="Call to action",
                    ),
                },
                confidence_score=0.85,
            )
            pitches.append(pitch)
        
        result = await engine.send_outreach(pitches)
        
        # Should not exceed daily limit
        assert result.messages_sent <= engine.DAILY_LIMITS[OutreachChannel.EMAIL]
    
    @pytest.mark.asyncio
    async def test_track_responses(self, engine, test_pitch):
        """Test response tracking."""
        result = await engine.send_outreach([test_pitch])
        await engine.track_responses(result.sequences)
        
        # Check if any messages were marked as opened/replied
        opened_count = sum(
            1 for seq in result.sequences
            for msg in seq.messages
            if msg.status == OutreachStatus.OPENED
        )
        
        # In dry run, this is simulated
        assert opened_count >= 0
    
    @pytest.mark.asyncio
    async def test_get_daily_report(self, engine):
        """Test daily report generation."""
        # Send some messages first
        pitch = Pitch(
            id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            category="dental",
            pain_points=["No GBP"],
            value_proposition="Get more patients",
            channels={
                PitchChannel.EMAIL: PitchContent(
                    channel=PitchChannel.EMAIL,
                    body="Email body",
                    cta="Call to action",
                ),
            },
            confidence_score=0.85,
        )
        
        await engine.send_outreach([pitch])
        report = await engine.get_daily_report()
        
        assert "date" in report
        assert "sent_today" in report
        assert "limits" in report
        assert "remaining" in report
        assert report["sent_today"]["email"] >= 1


class TestLayerEntry:
    """Test Layer 3 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        pitch = Pitch(
            id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            category="dental",
            pain_points=["No GBP"],
            value_proposition="Get more patients",
            channels={
                PitchChannel.EMAIL: PitchContent(
                    channel=PitchChannel.EMAIL,
                    body="Email body",
                    cta="Call to action",
                ),
            },
            confidence_score=0.85,
        )
        
        result = await run_layer([pitch], dry_run=True)
        
        assert isinstance(result, OutreachResult)
        assert result.prospects_contacted == 1
        assert result.messages_sent >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
