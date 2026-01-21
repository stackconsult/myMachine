from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from cep_deep_agent import cep_agent

app = FastAPI(title="CEP Machine Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CopilotKit runtime endpoints for Deep Agent
@app.post("/api/copilotkit")
async def copilotkit_runtime():
    """CopilotKit runtime endpoint for Deep Agent"""
    return JSONResponse(
        content={
            "agents": [
                {
                    "name": "cep_machine",
                    "description": "CEP Machine Deep Agent - 9-layer AI business automation framework",
                    "actions": [
                        {
                            "name": "search_prospects",
                            "description": "Search for businesses by location and category",
                            "parameters": ["location", "category"]
                        },
                        {
                            "name": "generate_pitch", 
                            "description": "Generate personalized outreach content",
                            "parameters": ["business_name", "industry"]
                        },
                        {
                            "name": "send_outreach",
                            "description": "Send outreach messages",
                            "parameters": ["contact_email", "message", "channel"]
                        },
                        {
                            "name": "optimize_gbp",
                            "description": "Optimize Google Business Profile",
                            "parameters": ["business_id", "updates"]
                        },
                        {
                            "name": "generate_report",
                            "description": "Generate performance reports",
                            "parameters": ["date_range", "metrics"]
                        },
                        {
                            "name": "track_finances",
                            "description": "Track financial transactions",
                            "parameters": ["transaction_type", "amount", "category"]
                        },
                        {
                            "name": "analyze_performance",
                            "description": "Analyze layer performance",
                            "parameters": ["layer_name", "time_period"]
                        }
                    ]
                }
            ]
        }
    )

@app.get("/api/copilotkit/info")
async def copilotkit_info():
    """CopilotKit info endpoint"""
    return JSONResponse(
        content={
            "agents": ["cep_machine"],
            "actions": [
                "search_prospects",
                "generate_pitch",
                "send_outreach", 
                "optimize_gbp",
                "generate_report",
                "track_finances",
                "analyze_performance"
            ]
        }
    )

@app.post("/api/copilotkit/agents/cep_machine/sync")
async def copilotkit_agent_sync():
    """Agent sync endpoint"""
    return JSONResponse(
        content={
            "name": "cep_machine",
            "description": "CEP Machine Deep Agent - 9-layer AI business automation framework"
        }
    )

@app.post("/api/copilotkit/agents/cep_machine/invoke")
async def copilotkit_agent_invoke(request: dict):
    """Agent invoke endpoint - this would integrate with the actual deep agent"""
    try:
        # For now, return a mock response
        # In production, this would call: await cep_agent.ainvoke(request.get("messages", []))
        return JSONResponse(
            content={
                "messages": [
                    {
                        "role": "assistant",
                        "content": "I'm the CEP Machine Deep Agent. I can help you with business automation using my 7 specialized tools. Try asking me to search for prospects, generate pitches, or analyze performance!"
                    }
                ]
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Agent invocation failed: {str(e)}"},
            status_code=500
        )

@app.get("/")
async def root():
    return {"message": "CEP Machine Backend API", "status": "running", "agent": "deep_agent_enabled"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cep-machine-backend", "agent": "deep_agent"}

@app.get("/api/layers")
async def get_layers():
    return {
        "layers": [
            {"id": 1, "name": "Prospect Research", "status": "active", "tools": ["search_prospects"]},
            {"id": 2, "name": "Pitch Generator", "status": "active", "tools": ["generate_pitch"]},
            {"id": 3, "name": "Outreach Engine", "status": "active", "tools": ["send_outreach"]},
            {"id": 4, "name": "Booking Handler", "status": "active", "tools": []},
            {"id": 5, "name": "Onboarding Flow", "status": "active", "tools": []},
            {"id": 6, "name": "GBP Optimizer", "status": "active", "tools": ["optimize_gbp"]},
            {"id": 7, "name": "Reporting Engine", "status": "active", "tools": ["generate_report", "analyze_performance"]},
            {"id": 8, "name": "Finance Tracker", "status": "active", "tools": ["track_finances"]},
            {"id": 9, "name": "Self-Learning", "status": "active", "tools": ["analyze_performance"]},
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
