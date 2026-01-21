"""
Prospect Research Agent - Layer 1
Integrates with existing CEP Machine prospector
Uses Supabase for storage and Dragonfly for caching
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
import asyncio
from typing import Dict, Any, List

# Import CEP Machine modules
from cep_machine.layers.prospector import ProspectResearchEngine
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache, cache_result, prospect_cache_key

@cache_result(ttl=3600, key_prefix="prospects")
async def search_businesses(query: str, location: str) -> List[Dict[str, Any]]:
    """Search for businesses using CEP Machine with caching"""
    engine = ProspectResearchEngine()
    
    # Use CEP's research capability
    prospects = await engine.search_prospects(
        query=query,
        location=location,
        limit=10
    )
    
    # Save to Supabase
    db = await get_database()
    for prospect in prospects:
        await db.save_prospect(prospect)
    
    return [
        {
            "name": p.get("business_name", "Unknown"),
            "location": p.get("location", location),
            "category": p.get("category", "Unknown"),
            "phone": p.get("phone", ""),
            "website": p.get("website", ""),
            "gbp_score": p.get("gbp_score", 0),
            "address": p.get("address", ""),
        }
        for p in prospects
    ]

async def analyze_gbp(business_name: str, location: str) -> Dict[str, Any]:
    """Analyze GBP for a business"""
    engine = ProspectResearchEngine()
    
    analysis = await engine.analyze_gbp(
        business_name=business_name,
        location=location
    )
    
    return {
        "profile_strength": analysis.get("profile_strength", 0),
        "review_count": analysis.get("review_count", 0),
        "rating": analysis.get("rating", 0),
        "issues": analysis.get("issues", []),
        "opportunities": analysis.get("opportunities", []),
    }

async def score_prospect(prospect_data: Dict[str, Any]) -> float:
    """Score a prospect using CEP Machine logic"""
    engine = ProspectResearchEngine()
    
    score = await engine.calculate_prospect_score(prospect_data)
    
    return score

def create_prospect_research_agent():
    """Create the prospect research agent"""
    
    system_prompt = """You are a B2B prospect research specialist for CEP Machine.
    
    Your capabilities:
    1. Search for businesses in specific locations and categories
    2. Analyze Google Business Profile (GBP) data
    3. Score prospects based on their potential value
    4. Identify opportunities for improvement
    
    When searching, always ask for:
    - Location (city, state, or region)
    - Category or industry
    - Any specific criteria
    
    Provide detailed analysis including:
    - Business contact information
    - GBP strength score (0-100)
    - Key issues and opportunities
    - Overall prospect score"""
    
    agent = create_deep_agent(
        model="openai:gpt-4o",
        tools=[
            search_businesses,
            analyze_gbp,
            score_prospect,
        ],
        middleware=[CopilotKitMiddleware()],
        system_prompt=system_prompt,
        name="prospect_research"
    )
    
    return agent
