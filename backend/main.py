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

from copilotkit import CopilotRuntime, OpenAIAdapter, AnthropicAdapter, GroqAdapter
from agents.prospect_research import create_prospect_research_agent
from agents.pitch_generator import create_pitch_generator_agent
from agents.outreach_engine import create_outreach_engine_agent
from agents.copilot_cloud_agents import (
    create_prospect_research_cloud_agent,
    create_pitch_generator_cloud_agent,
    create_outreach_engine_cloud_agent
)

# Import CEP Machine modules with Supabase
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

# Import model config API
from api.model_config import router as model_router
from api.websocket import router as websocket_router
from api.a2ui_generator import router as a2ui_router

app = FastAPI(title="CEP Machine API", version="1.0.0")

# Include routers
app.include_router(model_router)
app.include_router(websocket_router)
app.include_router(a2ui_router)

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
    global runtime, prospect_agent, pitch_agent, outreach_agent
    
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
        
        # Check CopilotKit Cloud
        if os.getenv("COPILOTKIT_API_KEY"):
            print("✅ CopilotKit Cloud API key configured")
        else:
            print("⚠️  CopilotKit Cloud API key not configured")
        
        # Create agents - Use Cloud agents if available, fallback to local
        USE_CLOUD_AGENTS = os.getenv("USE_CLOUD_AGENTS", "true").lower() == "true"
        
        if USE_CLOUD_AGENTS and os.getenv("COPILOTKIT_API_KEY"):
            print("🌐 Using CopilotKit Cloud agents")
            prospect_agent = await create_prospect_research_cloud_agent()
            pitch_agent = await create_pitch_generator_cloud_agent()
            outreach_agent = await create_outreach_engine_cloud_agent()
        else:
            print("🔧 Using local agents")
            prospect_agent = create_prospect_research_agent()
            pitch_agent = create_pitch_generator_agent()
            outreach_agent = create_outreach_engine_agent()
        
        # Configure CopilotKit runtime with multi-model support
        def get_model_adapter():
            """Get model adapter based on environment"""
            model_provider = os.getenv("MODEL_PROVIDER", "openai").lower()
            
            if model_provider == "anthropic":
                return AnthropicAdapter(api_key=os.getenv("ANTHROPIC_API_KEY"))
            elif model_provider == "groq":
                return GroqAdapter(api_key=os.getenv("GROQ_API_KEY"))
            else:
                return OpenAIAdapter(api_key=os.getenv("OPENAI_API_KEY"))
        
        runtime = CopilotRuntime(
            adapters=[get_model_adapter()],
            agents={
                "prospect_research": prospect_agent,
                "pitch_generator": pitch_agent,
                "outreach_engine": outreach_agent,
            }
        )
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        raise

# Global variables for agents and runtime
runtime = None
prospect_agent = None
pitch_agent = None
outreach_agent = None

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
