from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json

app = FastAPI(title="CEP Machine Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CopilotKit runtime endpoints
@app.post("/api/copilotkit")
async def copilotkit_runtime():
    """Basic CopilotKit runtime endpoint"""
    return JSONResponse(
        content={
            "agents": [
                {
                    "name": "default",
                    "description": "CEP Machine Assistant",
                    "actions": []
                }
            ]
        }
    )

@app.get("/api/copilotkit/info")
async def copilotkit_info():
    """CopilotKit info endpoint"""
    return JSONResponse(
        content={
            "agents": ["default"],
            "actions": []
        }
    )

@app.post("/api/copilotkit/agents/default/sync")
async def copilotkit_agent_sync():
    """Agent sync endpoint"""
    return JSONResponse(
        content={
            "name": "default",
            "description": "CEP Machine Assistant"
        }
    )

@app.post("/api/copilotkit/agents/default/invoke")
async def copilotkit_agent_invoke():
    """Agent invoke endpoint"""
    return JSONResponse(
        content={
            "messages": [
                {
                    "role": "assistant", 
                    "content": "I'm a CEP Machine assistant. I can help you with the 9-layer AI framework for business automation."
                }
            ]
        }
    )

@app.get("/")
async def root():
    return {"message": "CEP Machine Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cep-machine-backend"}

@app.get("/api/layers")
async def get_layers():
    return {
        "layers": [
            {"id": 1, "name": "Prospect Research", "status": "active"},
            {"id": 2, "name": "Pitch Generator", "status": "active"},
            {"id": 3, "name": "Outreach Engine", "status": "active"},
            {"id": 4, "name": "Booking Handler", "status": "active"},
            {"id": 5, "name": "Onboarding Flow", "status": "active"},
            {"id": 6, "name": "GBP Optimizer", "status": "active"},
            {"id": 7, "name": "Reporting Engine", "status": "active"},
            {"id": 8, "name": "Finance Tracker", "status": "active"},
            {"id": 9, "name": "Self-Learning", "status": "active"},
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
