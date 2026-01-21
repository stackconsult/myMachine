"""
CopilotKit Cloud Agents Integration
Uses pre-built Deep Agents from CopilotKit Cloud
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from copilotkit import CopilotRuntime, OpenAIAdapter, AnthropicAdapter, GroqAdapter
from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware
import asyncio
from typing import Dict, Any, List
import httpx

# Import CEP Machine modules
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class CopilotCloudAgent:
    """Wrapper for CopilotKit Cloud pre-built agents"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.cloud_url = os.getenv('COPILOTKIT_CLOUD_URL', 'https://cloud.copilotkit.ai')
        self.api_key = os.getenv('COPILOTKIT_API_KEY')
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent via CopilotKit Cloud"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.cloud_url}/api/v1/agents/{self.agent_id}/execute",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": input_data,
                    "agent_type": self.agent_type
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Agent execution failed: {response.text}")

# Pre-built CopilotKit Cloud Agents
CLOUD_AGENTS = {
    "research_agent": {
        "id": "research_agent_v1",
        "type": "deep_agent",
        "description": "Research agent with web search and analysis capabilities"
    },
    "analysis_agent": {
        "id": "analysis_agent_v1", 
        "type": "deep_agent",
        "description": "Data analysis and visualization agent"
    },
    "content_agent": {
        "id": "content_agent_v1",
        "type": "deep_agent", 
        "description": "Content generation and personalization agent"
    },
    "workflow_agent": {
        "id": "workflow_agent_v1",
        "type": "crewai_flow",
        "description": "Multi-step workflow orchestration agent"
    }
}

async def create_cloud_agent(agent_name: str, custom_tools: List = None):
    """Create a CopilotKit Cloud agent with custom tools"""
    
    if agent_name not in CLOUD_AGENTS:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    agent_config = CLOUD_AGENTS[agent_name]
    cloud_agent = CopilotCloudAgent(
        agent_id=agent_config["id"],
        agent_type=agent_config["type"]
    )
    
    # Create wrapper agent with CEP integration
    system_prompt = f"""You are a {agent_config['description']} integrated with CEP Machine.
    
    Your capabilities:
    - Access to CEP Machine's 9 business layers
    - Real-time data from Supabase
    - High-performance caching with DragonflyDB
    - Integration with existing CEP tools and workflows
    
    Always provide:
    - Clear step-by-step execution
    - Real-time progress updates
    - Results saved to Supabase
    - Cache optimization for repeated operations"""
    
    # Combine cloud agent with custom CEP tools
    tools = custom_tools or []
    
    # Add CEP-specific tools
    if agent_name == "research_agent":
        tools.extend([
            search_prospects_cloud,
            analyze_gbp_cloud,
            score_prospect_cloud
        ])
    elif agent_name == "content_agent":
        tools.extend([
            generate_pitch_cloud,
            personalize_content_cloud,
            analyze_pain_points_cloud
        ])
    elif agent_name == "workflow_agent":
        tools.extend([
            plan_outreach_sequence_cloud,
            execute_outreach_cloud,
            track_metrics_cloud
        ])
    
    agent = create_deep_agent(
        model="openai:gpt-4o",
        tools=tools,
        middleware=[CopilotKitMiddleware()],
        system_prompt=system_prompt,
        name=f"cep_{agent_name}"
    )
    
    return agent

# Cloud-integrated tools
async def search_prospects_cloud(query: str, location: str) -> List[Dict[str, Any]]:
    """Search prospects using cloud agent + CEP data"""
    # Use cloud agent for intelligent search
    cloud_agent = CopilotCloudAgent("research_agent_v1", "deep_agent")
    
    # Get cached results first
    cache = await get_cache()
    cache_key = f"cloud_prospects:{location}:{query}"
    cached = await cache.get(cache_key)
    
    if cached:
        return cached
    
    # Use cloud agent for analysis
    analysis = await cloud_agent.execute({
        "query": query,
        "location": location,
        "task": "prospect_research"
    })
    
    # Save to Supabase
    db = await get_database()
    prospects = []
    
    for result in analysis.get("results", []):
        prospect = await db.save_prospect({
            "business_name": result.get("name"),
            "location": location,
            "category": result.get("category"),
            "phone": result.get("phone"),
            "website": result.get("website"),
            "gbp_score": result.get("gbp_score", 0),
            "prospect_score": result.get("score", 0),
            "source": "copilot_cloud"
        })
        prospects.append(prospect)
    
    # Cache results
    await cache.set(cache_key, prospects, ttl=3600)
    
    return prospects

async def generate_pitch_cloud(prospect_data: Dict[str, Any], channel: str) -> Dict[str, Any]:
    """Generate pitch using cloud agent"""
    cloud_agent = CopilotCloudAgent("content_agent_v1", "deep_agent")
    
    # Get cached pitch template
    cache = await get_cache()
    cache_key = f"cloud_pitch:{prospect_data.get('id')}:{channel}"
    cached = await cache.get(cache_key)
    
    if cached:
        return cached
    
    # Generate with cloud agent
    pitch = await cloud_agent.execute({
        "prospect": prospect_data,
        "channel": channel,
        "task": "pitch_generation",
        "context": "cep_business_automation"
    })
    
    # Save to Supabase
    db = await get_database()
    saved_pitch = await db.save_pitch({
        "prospect_id": prospect_data.get("id"),
        "channel": channel,
        "subject": pitch.get("subject"),
        "body": pitch.get("body"),
        "confidence_score": pitch.get("confidence", 0.8),
        "template": "copilot_cloud",
        "status": "generated"
    })
    
    # Cache result
    await cache.set(cache_key, saved_pitch, ttl=86400)
    
    return saved_pitch

async def analyze_gbp_cloud(business_name: str, location: str) -> Dict[str, Any]:
    """Analyze GBP using cloud agent"""
    cloud_agent = CopilotCloudAgent("research_agent_v1", "deep_agent")
    
    analysis = await cloud_agent.execute({
        "business": business_name,
        "location": location,
        "task": "gbp_analysis",
        "depth": "comprehensive"
    })
    
    return {
        "profile_strength": analysis.get("profile_strength", 0),
        "review_count": analysis.get("review_count", 0),
        "rating": analysis.get("rating", 0),
        "issues": analysis.get("issues", []),
        "opportunities": analysis.get("opportunities", []),
        "recommendations": analysis.get("recommendations", [])
    }

async def score_prospect_cloud(prospect_data: Dict[str, Any]) -> float:
    """Score prospect using cloud agent"""
    cloud_agent = CopilotCloudAgent("analysis_agent_v1", "deep_agent")
    
    result = await cloud_agent.execute({
        "prospect": prospect_data,
        "task": "prospect_scoring",
        "model": "advanced"
    })
    
    return result.get("score", 0.5)

async def personalize_content_cloud(content: str, prospect_data: Dict[str, Any]) -> str:
    """Personalize content using cloud agent"""
    cloud_agent = CopilotCloudAgent("content_agent_v1", "deep_agent")
    
    result = await cloud_agent.execute({
        "content": content,
        "prospect": prospect_data,
        "task": "personalization",
        "tone": "professional"
    })
    
    return result.get("personalized_content", content)

async def analyze_pain_points_cloud(business_data: Dict[str, Any]) -> List[str]:
    """Analyze pain points using cloud agent"""
    cloud_agent = CopilotCloudAgent("research_agent_v1", "deep_agent")
    
    result = await cloud_agent.execute({
        "business": business_data,
        "task": "pain_point_analysis",
        "industry": business_data.get("category", "general")
    })
    
    return result.get("pain_points", [])

async def plan_outreach_sequence_cloud(prospect_data: Dict[str, Any], channels: List[str]) -> Dict[str, Any]:
    """Plan outreach sequence using cloud workflow agent"""
    cloud_agent = CopilotCloudAgent("workflow_agent_v1", "crewai_flow")
    
    sequence = await cloud_agent.execute({
        "prospect": prospect_data,
        "channels": channels,
        "task": "outreach_planning",
        "duration": "30_days"
    })
    
    return sequence

async def execute_outreach_cloud(sequence_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute outreach using cloud agent"""
    cloud_agent = CopilotCloudAgent("workflow_agent_v1", "crewai_flow")
    
    result = await cloud_agent.execute({
        "sequence": sequence_data,
        "task": "outreach_execution",
        "real_time": True
    })
    
    return result

async def track_metrics_cloud(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track metrics using cloud analysis agent"""
    cloud_agent = CopilotCloudAgent("analysis_agent_v1", "deep_agent")
    
    metrics = await cloud_agent.execute({
        "campaign": campaign_data,
        "task": "metrics_analysis",
        "insights": True
    })
    
    return metrics

# Factory functions for each layer
async def create_prospect_research_cloud_agent():
    """Create Layer 1 agent with CopilotKit Cloud"""
    return await create_cloud_agent("research_agent")

async def create_pitch_generator_cloud_agent():
    """Create Layer 2 agent with CopilotKit Cloud"""
    return await create_cloud_agent("content_agent")

async def create_outreach_engine_cloud_agent():
    """Create Layer 3 agent with CopilotKit Cloud"""
    return await create_cloud_agent("workflow_agent")
