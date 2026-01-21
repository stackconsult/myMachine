"""
Tests for Layer 2: Pitch Generator

Success Criteria: Pitch generation with confidence score 0.75+ and multi-channel output.
"""

import pytest
import asyncio
from datetime import datetime

from cep_machine.layers.pitch_gen import (
    Pitch,
    PitchChannel,
    PitchContent,
    PitchTone,
    PitchGenerationResult,
    PitchGeneratorEngine,
    run_layer,
)
from cep_machine.layers.prospector import Prospect, GBPAnalysis, ProspectScore


class TestPitchContent:
    """Test PitchContent data class."""
    
    def test_pitch_content_creation(self):
        """Test creating pitch content."""
        content = PitchContent(
            channel=PitchChannel.EMAIL,
            subject="Test Subject",
            headline="Test Headline",
            body="Test body content here",
            cta="Call to action",
        )
        
        assert content.channel == PitchChannel.EMAIL
        assert content.subject == "Test Subject"
        assert content.word_count == 4  # "Test body content here"
    
    def test_word_count_calculation(self):
        """Test word count is calculated correctly."""
        content = PitchContent(
            channel=PitchChannel.EMAIL,
            body="This is a test with five words",
        )
        assert content.word_count == 5


class TestPitch:
    """Test Pitch data class."""
    
    def test_pitch_creation(self):
        """Test creating a pitch."""
        channels = {
            PitchChannel.EMAIL: PitchContent(
                channel=PitchChannel.EMAIL,
                body="Email content",
            )
        }
        
        pitch = Pitch(
            id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            category="dental",
            pain_points=["No GBP", "No reviews"],
            value_proposition="Get more customers",
            channels=channels,
            confidence_score=0.85,
        )
        
        assert pitch.id == "pitch_001"
        assert pitch.business_name == "Test Business"
        assert pitch.confidence_score == 0.85
        assert len(pitch.channels) == 1
    
    def test_pitch_to_dict(self):
        """Test pitch serialization."""
        channels = {
            PitchChannel.EMAIL: PitchContent(
                channel=PitchChannel.EMAIL,
                body="Email content",
            )
        }
        
        pitch = Pitch(
            id="pitch_001",
            prospect_id="prospect_001",
            business_name="Test Business",
            category="dental",
            pain_points=["No GBP"],
            value_proposition="Get more customers",
            channels=channels,
            confidence_score=0.85,
        )
        
        data = pitch.to_dict()
        assert data["id"] == "pitch_001"
        assert data["confidence_score"] == 0.85
        assert "email" in data["channels"]


class TestPitchGeneratorEngine:
    """Test PitchGeneratorEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return PitchGeneratorEngine()
    
    @pytest.fixture
    def test_prospect(self):
        return Prospect(
            id="test_001",
            business_name="Test Dental",
            category="dental",
            location="Calgary, AB",
            gbp_analysis=GBPAnalysis(
                has_gbp=True,
                claimed=False,
                review_count=2,
                avg_rating=3.5,
                has_photos=False,
            ),
            score=ProspectScore.HOT,
            gbp_score=25,
            opportunities=["Claim GBP", "Add reviews", "Add photos"],
            estimated_revenue_loss=250000,
        )
    
    @pytest.mark.asyncio
    async def test_generate_pitch(self, engine, test_prospect):
        """Test generating a single pitch."""
        pitch = await engine.generate_pitch(test_prospect)
        
        assert isinstance(pitch, Pitch)
        assert pitch.business_name == "Test Dental"
        assert pitch.category == "dental"
        assert pitch.confidence_score >= 0.5
        assert len(pitch.channels) > 0
    
    @pytest.mark.asyncio
    async def test_pitch_channels(self, engine, test_prospect):
        """Test pitch generation for specific channels."""
        channels = [PitchChannel.EMAIL, PitchChannel.LINKEDIN]
        pitch = await engine.generate_pitch(test_prospect, channels=channels)
        
        assert len(pitch.channels) == 2
        assert PitchChannel.EMAIL in pitch.channels
        assert PitchChannel.LINKEDIN in pitch.channels
        assert PitchChannel.PHONE not in pitch.channels
    
    @pytest.mark.asyncio
    async def test_pain_points_identification(self, engine, test_prospect):
        """Test pain points are identified correctly."""
        pitch = await engine.generate_pitch(test_prospect)
        
        assert len(pitch.pain_points) > 0
        assert any("GBP" in pp for pp in pitch.pain_points)
    
    @pytest.mark.asyncio
    async def test_confidence_calculation(self, engine, test_prospect):
        """Test confidence score calculation."""
        pitch = await engine.generate_pitch(test_prospect)
        
        # Hot leads should have higher confidence
        assert pitch.confidence_score >= 0.7
    
    @pytest.mark.asyncio
    async def test_batch_generation(self, engine):
        """Test generating pitches for multiple prospects."""
        prospects = [
            Prospect(
                id=f"test_{i}",
                business_name=f"Test Business {i}",
                category="dental",
                location="Calgary, AB",
                gbp_analysis=GBPAnalysis(review_count=i),
                score=ProspectScore.WARM,
                gbp_score=40 + i * 10,
                opportunities=["Add reviews"],
                estimated_revenue_loss=100000,
            )
            for i in range(3)
        ]
        
        result = await engine.generate_batch_pitches(prospects)
        
        assert isinstance(result, PitchGenerationResult)
        assert result.prospects_pitched == 3
        assert result.pitches_generated == 3
        assert result.avg_confidence >= 0.5
    
    def test_value_proposition_by_category(self, engine):
        """Test value propositions by category."""
        dental_prop = engine.VALUE_PROPS.get("dental", "")
        assert "patients" in dental_prop.lower()
        
        hvac_prop = engine.VALUE_PROPS.get("hvac", "")
        assert "service calls" in hvac_prop.lower()


class TestLayerEntry:
    """Test Layer 2 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        prospects = [
            Prospect(
                id="test_001",
                business_name="Test Dental",
                category="dental",
                location="Calgary, AB",
                gbp_analysis=GBPAnalysis(),
                score=ProspectScore.WARM,
                gbp_score=40,
                opportunities=["Add reviews"],
                estimated_revenue_loss=100000,
            )
        ]
        
        result = await run_layer(prospects)
        
        assert isinstance(result, PitchGenerationResult)
        assert result.prospects_pitched == 1
        assert result.pitches_generated == 1
        assert result.avg_confidence >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
