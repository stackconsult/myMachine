"""
CEP Layer 3: Outreach Engine

Send personalized pitches via multiple channels (Email, LinkedIn, Phone).
Orchestrates multi-channel outreach with delays and response tracking.

Container Alignment: Sales
Φ Contribution: +0.08

Input: Pitches from Layer 2
Output: Sent messages + response tracking
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from .pitch_gen import Pitch, PitchChannel


class OutreachStatus(Enum):
    """Status of outreach messages."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


class OutreachChannel(Enum):
    """Channels for outreach delivery."""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    PHONE = "phone"
    SMS = "sms"


@dataclass
class OutreachMessage:
    """An individual outreach message."""
    id: str
    pitch_id: str
    prospect_id: str
    business_name: str
    channel: OutreachChannel
    subject: Optional[str] = None
    content: str = ""
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: OutreachStatus = OutreachStatus.PENDING
    delivery_details: Dict[str, Any] = field(default_factory=dict)
    response: Optional[str] = None
    response_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pitch_id": self.pitch_id,
            "prospect_id": self.prospect_id,
            "business_name": self.business_name,
            "channel": self.channel.value,
            "subject": self.subject,
            "content": self.content,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status.value,
            "delivery_details": self.delivery_details,
            "response": self.response,
            "response_time": self.response_time.isoformat() if self.response_time else None,
            "metadata": self.metadata,
        }


@dataclass
class OutreachSequence:
    """A sequence of outreach messages for a prospect."""
    prospect_id: str
    business_name: str
    messages: List[OutreachMessage]
    sequence_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_next_message(self) -> Optional[OutreachMessage]:
        """Get the next message to send."""
        for msg in self.messages:
            if msg.status == OutreachStatus.PENDING:
                return msg
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prospect_id": self.prospect_id,
            "business_name": self.business_name,
            "messages": [m.to_dict() for m in self.messages],
            "sequence_name": self.sequence_name,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class OutreachResult:
    """Result of outreach campaign."""
    prospects_contacted: int
    messages_sent: int
    messages_delivered: int
    messages_opened: int
    replies_received: int
    outreach_time_seconds: float
    sequences: List[OutreachSequence]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prospects_contacted": self.prospects_contacted,
            "messages_sent": self.messages_sent,
            "messages_delivered": self.messages_delivered,
            "messages_opened": self.messages_opened,
            "replies_received": self.replies_received,
            "outreach_time_seconds": self.outreach_time_seconds,
            "sequences": [s.to_dict() for s in self.sequences],
        }


class OutreachEngine:
    """
    Layer 3: Outreach Engine
    
    Sends pitches via multiple channels with intelligent scheduling.
    Tracks responses and manages follow-up sequences.
    """
    
    # Channel delay rules (in hours)
    CHANNEL_DELAYS = {
        OutreachChannel.EMAIL: 0,      # Immediate
        OutreachChannel.LINKEDIN: 24,  # 1 day after email
        OutreachChannel.PHONE: 72,     # 3 days after email
        OutreachChannel.SMS: 48,      # 2 days after email
    }
    
    # Daily sending limits
    DAILY_LIMITS = {
        OutreachChannel.EMAIL: 50,
        OutreachChannel.LINKEDIN: 25,
        OutreachChannel.PHONE: 20,
        OutreachChannel.SMS: 30,
    }
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run  # If True, don't actually send
        self.sent_today = {channel: 0 for channel in OutreachChannel}
    
    async def send_outreach(
        self,
        pitches: List[Pitch],
        channels: Optional[List[PitchChannel]] = None,
        start_immediately: bool = True,
    ) -> OutreachResult:
        """
        Send outreach for multiple pitches.
        
        Args:
            pitches: Pitches from Layer 2
            channels: Channels to use (default: all available)
            start_immediately: Send immediately or schedule
        
        Returns:
            OutreachResult with all tracking data
        """
        start_time = datetime.now()
        
        print(f"[Layer 3] Starting outreach for {len(pitches)} prospects")
        
        # Create sequences for each pitch
        sequences = []
        for pitch in pitches:
            sequence = await self._create_sequence(pitch, channels)
            sequences.append(sequence)
        
        # Send messages according to schedule
        if start_immediately:
            for sequence in sequences:
                await self._execute_sequence(sequence)
        
        # Calculate results
        messages_sent = sum(
            1 for seq in sequences
            for msg in seq.messages
            if msg.status in [OutreachStatus.SENT, OutreachStatus.DELIVERED]
        )
        
        messages_delivered = sum(
            1 for seq in sequences
            for msg in seq.messages
            if msg.status == OutreachStatus.DELIVERED
        )
        
        messages_opened = sum(
            1 for seq in sequences
            for msg in seq.messages
            if msg.status == OutreachStatus.OPENED
        )
        
        replies_received = sum(
            1 for seq in sequences
            for msg in seq.messages
            if msg.status == OutreachStatus.REPLIED
        )
        
        outreach_time = (datetime.now() - start_time).total_seconds()
        
        result = OutreachResult(
            prospects_contacted=len(pitches),
            messages_sent=messages_sent,
            messages_delivered=messages_delivered,
            messages_opened=messages_opened,
            replies_received=replies_received,
            outreach_time_seconds=outreach_time,
            sequences=sequences,
        )
        
        print(f"[Layer 3] Outreach complete")
        print(f"  - Messages sent: {messages_sent}")
        print(f"  - Replies: {replies_received}")
        print(f"  - Time: {outreach_time:.1f}s")
        
        return result
    
    async def _create_sequence(
        self,
        pitch: Pitch,
        channels: Optional[List[PitchChannel]] = None,
    ) -> OutreachSequence:
        """Create an outreach sequence for a pitch."""
        channels = channels or list(pitch.channels.keys())
        
        messages = []
        now = datetime.now()
        
        # Create messages for each channel
        for channel in channels:
            if channel not in pitch.channels:
                continue
            
            pitch_content = pitch.channels[channel]
            
            # Calculate send time based on delays
            delay_hours = self.CHANNEL_DELAYS.get(OutreachChannel(channel.value), 0)
            send_time = now + timedelta(hours=delay_hours)
            
            message = OutreachMessage(
                id=f"msg_{pitch.id}_{channel.value}_{now.strftime('%Y%m%d%H%M%S')}",
                pitch_id=pitch.id,
                prospect_id=pitch.prospect_id,
                business_name=pitch.business_name,
                channel=OutreachChannel(channel.value),
                subject=pitch_content.subject,
                content=pitch_content.body,
                scheduled_at=send_time,
                metadata={
                    "confidence_score": pitch.confidence_score,
                    "pain_points": pitch.pain_points,
                    "value_prop": pitch.value_proposition,
                },
            )
            
            messages.append(message)
        
        # Sort by scheduled time
        messages.sort(key=lambda m: m.scheduled_at or datetime.max)
        
        sequence = OutreachSequence(
            prospect_id=pitch.prospect_id,
            business_name=pitch.business_name,
            messages=messages,
            sequence_name=f"Sequence_{pitch.business_name}_{now.strftime('%Y%m%d')}",
        )
        
        return sequence
    
    async def _execute_sequence(self, sequence: OutreachSequence) -> None:
        """Execute an outreach sequence."""
        print(f"[Layer 3] Executing sequence for {sequence.business_name}")
        
        for message in sequence.messages:
            if message.status != OutreachStatus.PENDING:
                continue
            
            # Check if it's time to send
            if message.scheduled_at and message.scheduled_at > datetime.now():
                continue
            
            # Check daily limits
            if self.sent_today[message.channel] >= self.DAILY_LIMITS[message.channel]:
                print(f"[Layer 3] Daily limit reached for {message.channel.value}")
                break
            
            # Send the message
            await self._send_message(message)
            
            # Add delay between sends
            await asyncio.sleep(0.5)  # 0.5 second delay
    
    async def _send_message(self, message: OutreachMessage) -> None:
        """Send an individual message."""
        print(f"[Layer 3] Sending {message.channel.value} to {message.business_name}")
        
        if self.dry_run:
            # Simulate sending
            message.status = OutreachStatus.SENT
            message.sent_at = datetime.now()
            message.delivery_details = {
                "dry_run": True,
                "simulated": True,
            }
            self.sent_today[message.channel] += 1
            return
        
        # Actual sending logic would go here
        # For now, we simulate
        try:
            if message.channel == OutreachChannel.EMAIL:
                await self._send_email(message)
            elif message.channel == OutreachChannel.LINKEDIN:
                await self._send_linkedin(message)
            elif message.channel == OutreachChannel.PHONE:
                await self._send_phone(message)
            elif message.channel == OutreachChannel.SMS:
                await self._send_sms(message)
            
            message.status = OutreachStatus.SENT
            message.sent_at = datetime.now()
            self.sent_today[message.channel] += 1
            
            print(f"[Layer 3] ✓ Sent {message.channel.value}")
            
        except Exception as e:
            message.status = OutreachStatus.FAILED
            message.delivery_details = {"error": str(e)}
            print(f"[Layer 3] ✗ Failed to send {message.channel.value}: {e}")
    
    async def _send_email(self, message: OutreachMessage) -> None:
        """Send email message."""
        # In production, use Gmail API, SendGrid, etc.
        message.delivery_details = {
            "provider": "gmail_api",
            "from": "your-email@example.com",
            "to": "prospect@example.com",
        }
    
    async def _send_linkedin(self, message: OutreachMessage) -> None:
        """Send LinkedIn message."""
        # In production, use LinkedIn API or automation
        message.delivery_details = {
            "provider": "linkedin_api",
            "connection_id": "123456",
        }
    
    async def _send_phone(self, message: OutreachMessage) -> None:
        """Initiate phone call or leave voicemail."""
        # In production, use Twilio or similar
        message.delivery_details = {
            "provider": "twilio",
            "phone": "+1234567890",
            "type": "voicemail",
        }
    
    async def _send_sms(self, message: OutreachMessage) -> None:
        """Send SMS message."""
        # In production, use Twilio
        message.delivery_details = {
            "provider": "twilio",
            "phone": "+1234567890",
        }
    
    async def track_responses(self, sequences: List[OutreachSequence]) -> None:
        """Track responses to sent messages."""
        print(f"[Layer 3] Tracking responses for {len(sequences)} sequences")
        
        for sequence in sequences:
            for message in sequence.messages:
                if message.status == OutreachStatus.SENT:
                    # Simulate response tracking
                    # In production, check email opens, replies, etc.
                    if message.channel == OutreachChannel.EMAIL:
                        # Simulate 30% open rate, 10% reply rate
                        import random
                        if random.random() < 0.3:
                            message.status = OutreachStatus.OPENED
                        if random.random() < 0.1:
                            message.status = OutreachStatus.REPLIED
                            message.response = "Thanks for reaching out, I'm interested."
                            message.response_time = datetime.now()
    
    async def get_daily_report(self) -> Dict[str, Any]:
        """Get daily outreach report."""
        return {
            "date": datetime.now().date().isoformat(),
            "sent_today": {k.value: v for k, v in self.sent_today.items()},
            "limits": {k.value: v for k, v in self.DAILY_LIMITS.items()},
            "remaining": {
                k.value: self.DAILY_LIMITS[k] - self.sent_today[k]
                for k in OutreachChannel
            },
        }


# Layer 3 Entry Point
async def run_layer(
    pitches: List[Pitch],
    channels: Optional[List[PitchChannel]] = None,
    dry_run: bool = True,
) -> OutreachResult:
    """
    Main entry point for Layer 3: Outreach Engine
    
    Args:
        pitches: Pitches from Layer 2
        channels: Channels to use (default: all)
        dry_run: If True, simulate sending
    
    Returns:
        OutreachResult with tracking data
    """
    print(f"\n{'='*60}")
    print(f"[Layer 3] OUTREACH ENGINE")
    print(f"Pitches: {len(pitches)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    engine = OutreachEngine(dry_run=dry_run)
    result = await engine.send_outreach(pitches, channels)
    
    # Track responses
    await engine.track_responses(result.sequences)
    
    print(f"\n[Layer 3] ✓ Complete")
    print(f"  - Prospects contacted: {result.prospects_contacted}")
    print(f"  - Messages sent: {result.messages_sent}")
    print(f"  - Replies received: {result.replies_received}")
    print(f"  - Outreach time: {result.outreach_time_seconds:.1f}s")
    
    # Daily report
    daily_report = await engine.get_daily_report()
    print(f"\n[Layer 3] Daily Report:")
    for channel, sent in daily_report["sent_today"].items():
        remaining = daily_report["remaining"][channel]
        print(f"  {channel}: {sent}/{daily_report['limits'][channel]} ({remaining} remaining)")
    
    return result


# Export
__all__ = [
    "OutreachMessage",
    "OutreachSequence",
    "OutreachResult",
    "OutreachEngine",
    "OutreachStatus",
    "OutreachChannel",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    from .pitch_gen import Pitch, PitchChannel, PitchContent, PitchTone
    
    # Create test pitch
    test_pitch = Pitch(
        id="pitch_001",
        prospect_id="prospect_001",
        business_name="Test Dental Clinic",
        category="dental",
        pain_points=["No GBP", "No reviews"],
        value_proposition="Attract 20-30 new patients monthly",
        channels={
            PitchChannel.EMAIL: PitchContent(
                channel=PitchChannel.EMAIL,
                subject="Google visibility for Test Dental",
                body="Hi, I noticed your business could benefit from better Google visibility...",
                cta="Reply for your free audit",
            ),
            PitchChannel.LINKEDIN: PitchContent(
                channel=PitchChannel.LINKEDIN,
                body="Hi Test Dental, saw your business in Calgary...",
                cta="Open to a quick chat?",
            ),
        },
        confidence_score=0.85,
    )
    
    dry_run = "--live" not in sys.argv
    result = asyncio.run(run_layer([test_pitch], dry_run=dry_run))
    
    print("\n" + "="*60)
    print("OUTREACH SEQUENCES:")
    print("="*60)
    
    for seq in result.sequences:
        print(f"\nBusiness: {seq.business_name}")
        for msg in seq.messages:
            status_icon = "✓" if msg.status == OutreachStatus.SENT else "○"
            print(f"  {status_icon} {msg.channel.value}: {msg.status.value}")
            if msg.scheduled_at:
                print(f"    Scheduled: {msg.scheduled_at.strftime('%Y-%m-%d %H:%M')}")
