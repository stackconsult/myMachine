#!/usr/bin/env python3
"""
CEP Machine Backend with CopilotKit Integration
"""

import os
import sys
from pathlib import Path
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

app = FastAPI(title="CEP Machine API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "healthy", "agents": list(runtime.agents.keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
