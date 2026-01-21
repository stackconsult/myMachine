"""
CEP Layer 2: Pitch Generator

Generate personalized outreach pitches based on prospect research.
Takes Layer 1 output and creates multi-channel pitches.

Container Alignment: Sales
Φ Contribution: +0.08

Input: Prospect data from Layer 1
Output: Personalized pitches (email, LinkedIn, phone)
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

from .prospector import Prospect


class PitchChannel(Enum):
    """Channels for pitch delivery."""
    EMAIL = "email"
    LINKEDIN = "linkedin"
    PHONE = "phone"
    SMS = "sms"


class PitchTone(Enum):
    """Tone variations for pitches."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    DIRECT = "direct"
    CONSULTATIVE = "consultative"


@dataclass
class PitchContent:
    """Content for a specific channel."""
    channel: PitchChannel
    subject: Optional[str] = None  # For email
    headline: str = ""
    body: str = ""
    cta: str = ""
    word_count: int = 0
    
    def __post_init__(self):
        self.word_count = len(self.body.split())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel": self.channel.value,
            "subject": self.subject,
            "headline": self.headline,
            "body": self.body,
            "cta": self.cta,
            "word_count": self.word_count,
        }


@dataclass
class Pitch:
    """Complete pitch for a prospect."""
    id: str
    prospect_id: str
    business_name: str
    category: str
    pain_points: List[str]
    value_proposition: str
    channels: Dict[PitchChannel, PitchContent]
    confidence_score: float
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "business_name": self.business_name,
            "category": self.category,
            "pain_points": self.pain_points,
            "value_proposition": self.value_proposition,
            "channels": {k.value: v.to_dict() for k, v in self.channels.items()},
            "confidence_score": self.confidence_score,
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass
class PitchGenerationResult:
    """Result of batch pitch generation."""
    prospects_pitched: int
    pitches_generated: int
    avg_confidence: float
    generation_time_seconds: float
    pitches: List[Pitch]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prospects_pitched": self.prospects_pitched,
            "pitches_generated": self.pitches_generated,
            "avg_confidence": self.avg_confidence,
            "generation_time_seconds": self.generation_time_seconds,
            "pitches": [p.to_dict() for p in self.pitches],
        }


class PitchGeneratorEngine:
    """
    Layer 2: Pitch Generator Engine
    
    Creates personalized pitches based on prospect research.
    Uses LLM for content generation with fallback templates.
    """
    
    # Channel-specific word limits
    WORD_LIMITS = {
        PitchChannel.EMAIL: 150,
        PitchChannel.LINKEDIN: 100,
        PitchChannel.PHONE: 200,
        PitchChannel.SMS: 50,
    }
    
    # Industry-specific value propositions
    VALUE_PROPS = {
        "dental": "Attract 20-30 new patients monthly through Google visibility",
        "hvac": "Generate 50+ qualified service calls each month",
        "plumbing": "Book 15+ emergency jobs weekly from local searches",
        "electrician": "Secure 25+ residential projects monthly",
        "roofing": "Fill your pipeline with 10+ high-value roof replacements",
        "landscaping": "Book 20+ lawn care projects per week",
        "auto repair": "Drive 30+ service bookings from local customers",
        "chiropractor": "Attract 40+ new patient appointments monthly",
        "veterinarian": "Book 50+ pet appointments from local searches",
        "real estate": "Generate 100+ qualified buyer leads monthly",
        "attorney": "Secure 20+ case consultations from local searches",
        "accountant": "Attract 15+ new business clients quarterly",
        "restaurant": "Fill 100+ tables weekly from Google visibility",
        "salon": "Book 50+ appointments daily from local searches",
        "spa": "Attract 30+ wellness clients weekly",
        "gym": "Generate 40+ new member signups monthly",
        "fitness": "Book 60+ personal training sessions weekly",
    }
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4-turbo-preview"):
        self.llm_provider = llm_provider
        self.model = model
        self.llm = self._init_llm()
    
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
    
    async def generate_pitch(
        self,
        prospect: Prospect,
        channels: Optional[List[PitchChannel]] = None,
        tone: PitchTone = PitchTone.PROFESSIONAL,
    ) -> Pitch:
        """
        Generate a complete pitch for a prospect.
        
        Args:
            prospect: Prospect data from Layer 1
            channels: Channels to generate for (default: all)
            tone: Tone for the pitch
        
        Returns:
            Complete Pitch with all channel content
        """
        channels = channels or list(PitchChannel)
        
        print(f"[Layer 2] Generating pitch for {prospect.business_name}")
        
        # Identify pain points
        pain_points = self._identify_pain_points(prospect)
        
        # Create value proposition
        value_prop = self._create_value_proposition(prospect)
        
        # Generate content for each channel
        channel_content = {}
        for channel in channels:
            content = await self._generate_channel_content(
                prospect, channel, pain_points, value_prop, tone
            )
            channel_content[channel] = content
        
        # Calculate confidence score
        confidence = self._calculate_confidence(prospect, channel_content)
        
        pitch = Pitch(
            id=f"pitch_{prospect.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            prospect_id=prospect.id,
            business_name=prospect.business_name,
            category=prospect.category,
            pain_points=pain_points,
            value_proposition=value_prop,
            channels=channel_content,
            confidence_score=confidence,
            metadata={"tone": tone.value, "channels": [c.value for c in channels]},
        )
        
        print(f"[Layer 2] ✓ Pitch generated (confidence: {confidence:.2f})")
        
        return pitch
    
    def _identify_pain_points(self, prospect: Prospect) -> List[str]:
        """Identify pain points based on GBP analysis."""
        pain_points = []
        
        if not prospect.gbp_analysis.has_gbp:
            pain_points.append("No Google Business Profile - invisible to local searches")
        
        if not prospect.gbp_analysis.claimed:
            pain_points.append("Unclaimed GBP - competitors can hijack your listing")
        
        if prospect.gbp_analysis.review_count < 10:
            pain_points.append(f"Only {prospect.gbp_analysis.review_count} reviews - low trust")
        
        if prospect.gbp_analysis.avg_rating < 4.0:
            pain_points.append(f"Rating {prospect.gbp_analysis.avg_rating} - deterring customers")
        
        if not prospect.gbp_analysis.has_photos:
            pain_points.append("No photos - unprofessional appearance")
        
        if not prospect.gbp_analysis.has_posts:
            pain_points.append("No recent activity - appears inactive")
        
        if not prospect.gbp_analysis.has_hours:
            pain_points.append("No business hours - customers can't visit")
        
        # Add revenue-based pain point
        if prospect.estimated_revenue_loss > 100000:
            pain_points.append(f"Losing ~${prospect.estimated_revenue_loss/1000:.0f}K annually from poor visibility")
        
        return pain_points[:3]  # Top 3 pain points
    
    def _create_value_proposition(self, prospect: Prospect) -> str:
        """Create a compelling value proposition."""
        # Get industry-specific value prop
        base_prop = self.VALUE_PROPS.get(prospect.category.lower(), "Increase your customer base through Google visibility")
        
        # Customize based on opportunities
        if "Create Google Business Profile" in prospect.opportunities:
            return f"Get found by local customers with a professional Google Business Profile. {base_prop}"
        
        if prospect.gbp_score < 30:
            return f"Transform your online presence and {base_prop.lower()}. We'll fix what's missing."
        
        return base_prop
    
    async def _generate_channel_content(
        self,
        prospect: Prospect,
        channel: PitchChannel,
        pain_points: List[str],
        value_prop: str,
        tone: PitchTone,
    ) -> PitchContent:
        """Generate content for a specific channel."""
        word_limit = self.WORD_LIMITS[channel]
        
        if self.llm:
            content = await self._llm_generate_content(
                prospect, channel, pain_points, value_prop, tone, word_limit
            )
        else:
            content = self._template_generate_content(
                prospect, channel, pain_points, value_prop, tone, word_limit
            )
        
        return content
    
    async def _llm_generate_content(
        self,
        prospect: Prospect,
        channel: PitchChannel,
        pain_points: List[str],
        value_prop: str,
        tone: PitchTone,
        word_limit: int,
    ) -> PitchContent:
        """Generate content using LLM."""
        channel_instructions = {
            PitchChannel.EMAIL: "Write a professional email with subject line",
            PitchChannel.LINKEDIN: "Write a LinkedIn message (more casual)",
            PitchChannel.PHONE: "Write a phone script (conversational)",
            PitchChannel.SMS: "Write a short SMS text message",
        }
        
        prompt = f"""Generate a {tone.value} pitch for a {prospect.category} business.

Business: {prospect.business_name}
Location: {prospect.location}
Pain Points: {', '.join(pain_points)}
Value Proposition: {value_prop}

Instructions: {channel_instructions.get(channel, '')}
Word limit: {word_limit} words

Include a clear call-to-action.

Format: Return JSON with {{"subject": "...", "headline": "...", "body": "...", "cta": "..."}}"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            content = json.loads(response.content)
            
            return PitchContent(
                channel=channel,
                subject=content.get("subject") if channel == PitchChannel.EMAIL else None,
                headline=content.get("headline", ""),
                body=content.get("body", ""),
                cta=content.get("cta", ""),
            )
            
        except Exception as e:
            print(f"[Layer 2] LLM generation failed: {e}")
            return self._template_generate_content(
                prospect, channel, pain_points, value_prop, tone, word_limit
            )
    
    def _template_generate_content(
        self,
        prospect: Prospect,
        channel: PitchChannel,
        pain_points: List[str],
        value_prop: str,
        tone: PitchTone,
        word_limit: int,
    ) -> PitchContent:
        """Generate content using templates (fallback)."""
        # Simple template-based generation
        headline = f"Improve your Google visibility"
        
        if channel == PitchChannel.EMAIL:
            subject = f"Google visibility for {prospect.business_name}"
            body = f"""Hi {prospect.business_name},

I noticed your business could benefit from better Google visibility. {value_prop}.

Key issues I found:
{chr(10).join(f"- {p}" for p in pain_points[:2])}

Would you be interested in a free GBP audit?

Best regards"""
            cta = "Reply for your free audit"
        
        elif channel == PitchChannel.LINKEDIN:
            body = f"""Hi {prospect.business_name}, saw your {prospect.category} business in {prospect.location.split(',')[0]}. {value_prop}. You're missing out on local customers due to weak Google presence. Happy to share what's working for similar businesses."""
            cta = "Open to a quick chat?"
        
        elif channel == PitchChannel.PHONE:
            body = f"""Hi, this is [Name]. I found {prospect.business_name} on Google and noticed you might be losing customers to competitors. {value_prop}. Do you have 5 minutes to hear how we're helping other {prospect.category} businesses in {prospect.location.split(',')[0]}?"""
            cta = "Schedule a 15-minute call"
        
        else:  # SMS
            body = f"Hi {prospect.business_name}, this is [Name]. Noticed your Google listing needs optimization. {value_prop}. Interested in a free audit?"
            cta = "Reply YES"
        
        # Truncate to word limit
        words = body.split()
        if len(words) > word_limit:
            body = " ".join(words[:word_limit])
        
        return PitchContent(
            channel=channel,
            subject=subject if channel == PitchChannel.EMAIL else None,
            headline=headline,
            body=body,
            cta=cta,
        )
    
    def _calculate_confidence(
        self,
        prospect: Prospect,
        channels: Dict[PitchChannel, PitchContent],
    ) -> float:
        """Calculate pitch confidence score."""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for weaker GBP
        if prospect.gbp_score < 30:
            confidence += 0.3
        elif prospect.gbp_score < 60:
            confidence += 0.2
        else:
            confidence += 0.1
        
        # Higher confidence for more opportunities
        if len(prospect.opportunities) >= 3:
            confidence += 0.1
        
        # Higher confidence for revenue loss
        if prospect.estimated_revenue_loss > 100000:
            confidence += 0.1
        
        # Check content quality
        for content in channels.values():
            if content.word_count >= self.WORD_LIMITS[content.channel] * 0.8:
                confidence += 0.05
            if "free" in content.body.lower() or "audit" in content.body.lower():
                confidence += 0.05
        
        return min(1.0, confidence)
    
    async def generate_batch_pitches(
        self,
        prospects: List[Prospect],
        channels: Optional[List[PitchChannel]] = None,
    ) -> PitchGenerationResult:
        """
        Generate pitches for multiple prospects.
        
        Args:
            prospects: List of prospects from Layer 1
            channels: Channels to generate for
        
        Returns:
            Batch generation result with all pitches
        """
        start_time = datetime.now()
        
        print(f"[Layer 2] Generating {len(prospects)} pitches...")
        
        pitches = []
        total_confidence = 0
        
        for prospect in prospects:
            pitch = await self.generate_pitch(prospect, channels)
            pitches.append(pitch)
            total_confidence += pitch.confidence_score
        
        generation_time = (datetime.now() - start_time).total_seconds()
        avg_confidence = total_confidence / len(pitches) if pitches else 0
        
        result = PitchGenerationResult(
            prospects_pitched=len(prospects),
            pitches_generated=len(pitches),
            avg_confidence=avg_confidence,
            generation_time_seconds=generation_time,
            pitches=pitches,
        )
        
        print(f"[Layer 2] ✓ Batch complete: {len(pitches)} pitches in {generation_time:.1f}s")
        print(f"  Average confidence: {avg_confidence:.2f}")
        
        return result


# Layer 2 Entry Point
async def run_layer(
    prospects: List[Prospect],
    channels: Optional[List[PitchChannel]] = None,
) -> PitchGenerationResult:
    """
    Main entry point for Layer 2: Pitch Generator
    
    Args:
        prospects: List of prospects from Layer 1
        channels: Channels to generate (default: all)
    
    Returns:
        PitchGenerationResult with all generated pitches
    """
    print(f"\n{'='*60}")
    print(f"[Layer 2] PITCH GENERATOR")
    print(f"Prospects: {len(prospects)}")
    print(f"{'='*60}\n")
    
    engine = PitchGeneratorEngine()
    result = await engine.generate_batch_pitches(prospects, channels)
    
    print(f"\n[Layer 2] ✓ Complete")
    print(f"  - Pitches generated: {result.pitches_generated}")
    print(f"  - Average confidence: {result.avg_confidence:.2f}")
    print(f"  - Generation time: {result.generation_time_seconds:.1f}s")
    
    return result


# Export
__all__ = [
    "Pitch",
    "PitchChannel",
    "PitchContent",
    "PitchTone",
    "PitchGenerationResult",
    "PitchGeneratorEngine",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    from .prospector import Prospect, GBPAnalysis, ProspectScore
    
    # Create test prospect
    test_prospect = Prospect(
        id="test_001",
        business_name="Test Dental Clinic",
        category="dental",
        location="Calgary, AB",
        gbp_analysis=GBPAnalysis(has_gbp=True, claimed=False, review_count=2),
        score=ProspectScore.HOT,
        gbp_score=25,
        opportunities=["Claim GBP", "Add more reviews", "Add photos"],
        estimated_revenue_loss=250000,
    )
    
    result = asyncio.run(run_layer([test_prospect]))
    
    print("\n" + "="*60)
    print("GENERATED PITCH:")
    print("="*60)
    
    if result.pitches:
        pitch = result.pitches[0]
        print(f"\nBusiness: {pitch.business_name}")
        print(f"Confidence: {pitch.confidence_score:.2f}")
        print(f"\nPain Points:")
        for pp in pitch.pain_points:
            print(f"  - {pp}")
        print(f"\nValue Prop: {pitch.value_proposition}")
        
        for channel, content in pitch.channels.items():
            print(f"\n{channel.value.upper()}:")
            if content.subject:
                print(f"  Subject: {content.subject}")
            print(f"  {content.body}")
            print(f"  CTA: {content.cta}")
