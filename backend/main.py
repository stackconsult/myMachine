#!/usr/bin/env python3
"""
CEP Machine Backend with CopilotKit Integration
Uses Supabase for database and DragonflyDB for caching
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Add parent directory to path for CEP modules
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from copilotkit import CopilotRuntime, OpenAIAdapter
from agents.prospect_research import create_prospect_research_agent
from agents.pitch_generator import create_pitch_generator_agent
from agents.outreach_engine import create_outreach_engine_agent

# Import CEP Machine modules with Supabase
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

app = FastAPI(title="CEP Machine API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and cache
@app.on_event("startup")
async def startup_event():
    """Initialize database and cache on startup"""
    try:
        # Initialize Supabase
        db = await get_database()
        print("✅ Supabase database connected")
        
        # Initialize DragonflyDB cache
        cache = await get_cache()
        print("✅ DragonflyDB cache connected")
        
        # Get cache info
        cache_info = await cache.get_info()
        print(f"   Cache version: {cache_info.get('version', 'Unknown')}")
        print(f"   Memory usage: {cache_info.get('used_memory_human', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        raise

# Create agents
prospect_agent = create_prospect_research_agent()
pitch_agent = create_pitch_generator_agent()
outreach_agent = create_outreach_engine_agent()

# Configure CopilotKit runtime
runtime = CopilotRuntime(
    adapters=[OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))],
    agents={
        "prospect_research": prospect_agent,
        "pitch_generator": pitch_agent,
        "outreach_engine": outreach_agent,
    }
)

@app.post("/api/copilotkit")
async def copilot_endpoint(request):
    """Handle CopilotKit requests"""
    return await runtime.handle_request(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": list(runtime.agents.keys()),
        "database": "supabase",
        "cache": "dragonfly"
    }

@app.get("/status")
async def get_status():
    """Get detailed system status"""
    try:
        # Get database status
        db = await get_database()
        coherence = await db.get_latest_coherence()
        
        # Get cache status
        cache = await get_cache()
        cache_info = await cache.get_info()
        
        return {
            "coherence": coherence,
            "cache": cache_info,
            "agents": list(runtime.agents.keys()),
            "timestamp": str(datetime.utcnow())
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
