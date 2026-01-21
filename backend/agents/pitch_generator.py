"""
Pitch Generator Agent - Layer 2
Integrates with existing CEP Machine pitch generator
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
import asyncio
from typing import Dict, Any

# Import CEP Machine modules
from cep_machine.layers.pitch_gen import PitchGeneratorEngine

async def generate_pitch(prospect_data: Dict[str, Any], channel: str = "email") -> Dict[str, Any]:
    """Generate personalized pitch using CEP Machine"""
    engine = PitchGeneratorEngine()
    
    pitch = await engine.generate_pitch(
        prospect_data=prospect_data,
        channel=channel
    )
    
    return pitch

async def analyze_pain_points(business_data: Dict[str, Any]) -> List[str]:
    """Analyze pain points for a business"""
    engine = PitchGeneratorEngine()
    
    pain_points = await engine.identify_pain_points(business_data)
    
    return pain_points

async def create_value_proposition(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create value proposition"""
    engine = PitchGeneratorEngine()
    
    value_prop = await engine.create_value_proposition(prospect_data)
    
    return value_prop

async def calculate_confidence(pitch_data: Dict[str, Any]) -> float:
    """Calculate pitch confidence score"""
    engine = PitchGeneratorEngine()
    
    confidence = await engine.calculate_pitch_confidence(pitch_data)
    
    return confidence

def create_pitch_generator_agent():
    """Create the pitch generator agent"""
    
    system_prompt = """You are an expert at creating personalized business pitches for CEP Machine.
    
    Your capabilities:
    1. Generate personalized pitches for different channels (email, LinkedIn, SMS)
    2. Analyze business pain points
    3. Create compelling value propositions
    4. Calculate pitch confidence scores
    
    When generating pitches, always ask for:
    - Prospect information (name, business, industry)
    - Channel preference (email, LinkedIn, SMS, phone)
    - Specific goals or objectives
    
    Provide:
    - Personalized subject lines
    - Compelling opening hooks
    - Clear value propositions
    - Strong call-to-actions
    - Confidence scores (0-100)"""
    
    agent = create_deep_agent(
        model="openai:gpt-4o",
        tools=[
            generate_pitch,
            analyze_pain_points,
            create_value_proposition,
            calculate_confidence,
        ],
        middleware=[CopilotKitMiddleware()],
        system_prompt=system_prompt,
        name="pitch_generator"
    )
    
    return agent
