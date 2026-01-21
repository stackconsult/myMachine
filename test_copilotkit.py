#!/usr/bin/env python3
"""
Test CopilotKit Integration
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.prospect_research import create_prospect_research_agent
from backend.agents.pitch_generator import create_pitch_generator_agent
from backend.agents.outreach_engine import create_outreach_engine_agent

async def test_agents():
    """Test all CopilotKit agents"""
    print("🧪 Testing CopilotKit Agents...")
    
    # Test prospect research agent
    print("\n1. Testing Prospect Research Agent...")
    prospect_agent = create_prospect_research_agent()
    print(f"   ✅ Agent created: {prospect_agent.name}")
    print(f"   📦 Tools: {len(prospect_agent.tools)}")
    
    # Test pitch generator agent
    print("\n2. Testing Pitch Generator Agent...")
    pitch_agent = create_pitch_generator_agent()
    print(f"   ✅ Agent created: {pitch_agent.name}")
    print(f"   📦 Tools: {len(pitch_agent.tools)}")
    
    # Test outreach engine agent
    print("\n3. Testing Outreach Engine Agent...")
    outreach_agent = create_outreach_engine_agent()
    print(f"   ✅ Agent created: {outreach_agent.name}")
    print(f"   📦 Tools: {len(outreach_agent.tools)}")
    
    print("\n✅ All agents created successfully!")
    print("\nNext steps:")
    print("   1. Set up API keys in backend/.env")
    print("   2. Run './start.sh' to start the application")
    print("   3. Open http://localhost:3000 to interact with agents")

if __name__ == "__main__":
    asyncio.run(test_agents())
