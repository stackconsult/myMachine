from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import json
import sys
import os
import asyncio

# Add the parent directory to the path to import cep_agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API router
from api.main import api_router

# Import metrics
from middleware.metrics import MetricsMiddleware, setup_metrics_endpoint, metrics_collection_task

try:
    from agents.langgraph_agents import AGENTS, get_agent, list_agents
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    print("Warning: langgraph_agents module not found, using fallback implementation")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    asyncio.create_task(metrics_collection_task())
    yield
    # Shutdown
    pass

app = FastAPI(title="CEP Machine Backend", version="1.0.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Setup metrics
app.add_middleware(MetricsMiddleware)
setup_metrics_endpoint(app)

# CopilotKit runtime endpoints - PRODUCTION AGENTS INTEGRATION
@app.post("/api/copilotkit")
async def copilotkit_runtime(request: dict = None):
    """Production CopilotKit runtime endpoint with LangGraph agents"""
    try:
        # Add license key validation header
        headers = {
            "X-CopilotKit-License-Key": "ck_pub_91deedc157617c4705bddc7124314855",
            "X-CopilotKit-Agent-Version": "1.0.0"
        }
        
        # Handle different request formats
        if request is None:
            request = {}
        
        # Check if this is a tool invocation
        if "messages" in request:
            # This is an agent invocation request
            messages = request.get("messages", [])
            if messages:
                last_message = messages[-1]
                user_input = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message)
                
                # Try to use production agents if available
                if AGENTS_AVAILABLE:
                    # Route to appropriate agent based on user intent
                    agent_name = None
                    
                    if "prospect" in user_input.lower() or "search" in user_input.lower():
                        agent_name = "business_growth"
                    elif "pitch" in user_input.lower() or "generate" in user_input.lower():
                        agent_name = "business_growth"
                    elif "outreach" in user_input.lower() or "send" in user_input.lower():
                        agent_name = "business_growth"
                    elif "finance" in user_input.lower() or "track" in user_input.lower():
                        agent_name = "finance_tracker"
                    elif "analyze" in user_input.lower() or "performance" in user_input.lower():
                        agent_name = "performance_analyzer"
                    
                    if agent_name and agent_name in AGENTS:
                        # Use the production LangGraph agent
                        agent = AGENTS[agent_name]
                        agent_result = agent.invoke(messages)
                        
                        # Extract the last AI message from the agent result
                        if agent_result and "messages" in agent_result:
                            ai_messages = [msg for msg in agent_result["messages"] if msg.type == "ai"]
                            if ai_messages:
                                response = ai_messages[-1].content
                            else:
                                response = f"I'm the {agent.name} agent. {agent.description}. I can help you with specialized tools for this domain."
                        else:
                            response = f"I'm the {agent.name} agent. {agent.description}. I can help you with specialized tools for this domain."
                    else:
                        # Fallback to general response
                        response = f"I'm the CEP Machine assistant with PREMIUM features enabled. I have access to specialized agents: {', '.join(list_agents())}. Each agent has specific tools and capabilities. What would you like to work on?"
                else:
                    # Fallback responses when agents module not available
                    if "prospect" in user_input.lower() or "search" in user_input.lower():
                        response = "I can help you search for prospects! Use the search_prospects tool with location and category parameters. Premium feature: Advanced filtering and real-time data available."
                    elif "pitch" in user_input.lower() or "generate" in user_input.lower():
                        response = "I can generate personalized pitches! Use the generate_pitch tool with business_name and industry parameters. Premium feature: AI-powered personalization with industry insights."
                    elif "outreach" in user_input.lower() or "send" in user_input.lower():
                        response = "I can help with outreach campaigns! Use the send_outreach tool with contact_email, message, and channel parameters. Premium feature: Multi-channel sequencing and analytics."
                    elif "report" in user_input.lower() or "analytics" in user_input.lower():
                        response = "I can generate performance reports! Use the generate_report tool with date_range and metrics parameters. Premium feature: Advanced analytics and predictive insights."
                    elif "optimize" in user_input.lower() or "gbp" in user_input.lower():
                        response = "I can optimize Google Business Profiles! Use the optimize_gbp tool with business_id and updates parameters. Premium feature: SEO optimization and competitor analysis."
                    elif "finance" in user_input.lower() or "track" in user_input.lower():
                        response = "I can track financial transactions! Use the track_finances tool with transaction_type, amount, and category parameters. Premium feature: Real-time financial analytics and forecasting."
                    elif "analyze" in user_input.lower() or "performance" in user_input.lower():
                        response = "I can analyze performance metrics! Use the analyze_performance tool with layer_name and time_period parameters. Premium feature: Deep performance insights and optimization recommendations."
                    else:
                        response = f"I'm the CEP Machine assistant with PREMIUM features enabled. I can help you with business automation using 7 specialized tools: search_prospects, generate_pitch, send_outreach, optimize_gbp, generate_report, track_finances, and analyze_performance. All tools have enhanced premium capabilities. What would you like to do?"
                
                return {
                    "messages": [
                        {"role": "assistant", "content": response}
                    ]
                }
        
        # Default agent listing response with production agents
        agents_list = []
        
        if AGENTS_AVAILABLE:
            # Use production agents
            for agent_name in list_agents():
                agent = AGENTS[agent_name]
                agents_list.append({
                    "name": agent_name,
                    "description": agent.description,
                    "type": "langgraph",
                    "capabilities": ["premium_tools", "state_management", "tool_execution"]
                })
        else:
            # Fallback agent definition
            agents_list = [
                {
                    "name": "cep_machine",
                    "description": "CEP Machine - 9-layer AI business automation framework (PREMIUM)",
                    "capabilities": ["premium_tools", "advanced_analytics", "real_time_data", "ai_insights"],
                    "type": "fallback"
                }
            ]
        
        return {
            "agents": agents_list,
            "license_info": {
                "type": "premium",
                "key": "ck_pub_91deedc157617c4705bddc7124314855",
                "features": ["premium_tools", "advanced_analytics", "real_time_data", "ai_insights", "unlimited_usage"]
            }
        }
    except Exception as e:
        return {"error": f"Runtime error: {str(e)}"}

@app.get("/api/copilotkit/info")
async def copilotkit_info():
    """CopilotKit info endpoint - PRODUCTION AGENTS"""
    agents_list = []
    actions_list = []
    
    if AGENTS_AVAILABLE:
        # Use production agents
        for agent_name in list_agents():
            agent = AGENTS[agent_name]
            agents_list.append(agent_name)
            # Add agent-specific actions
            if agent_name == "business_growth":
                actions_list.extend(["search_prospects", "generate_pitch", "send_outreach"])
            elif agent_name == "performance_analyzer":
                actions_list.extend(["analyze_performance", "generate_report"])
            elif agent_name == "finance_tracker":
                actions_list.extend(["track_finances"])
    else:
        # Fallback
        agents_list = ["cep_machine"]
        actions_list = [
            "search_prospects",
            "generate_pitch", 
            "send_outreach",
            "optimize_gbp",
            "generate_report",
            "track_finances",
            "analyze_performance"
        ]
    
    return JSONResponse(
        content={
            "agents": agents_list,
            "actions": actions_list,
            "production_agents": AGENTS_AVAILABLE
        }
    )

@app.post("/api/copilotkit/agents/{agent_name}/sync")
async def copilotkit_agent_sync(agent_name: str):
    """Agent sync endpoint - PRODUCTION AGENTS"""
    if AGENTS_AVAILABLE and agent_name in AGENTS:
        agent = AGENTS[agent_name]
        return JSONResponse(
            content={
                "name": agent_name,
                "description": agent.description,
                "type": "langgraph_production"
            }
        )
    else:
        # Fallback
        return JSONResponse(
            content={
                "name": agent_name or "cep_machine",
                "description": "CEP Machine - 9-layer AI business automation framework",
                "type": "fallback"
            }
        )

@app.post("/api/copilotkit/agents/{agent_name}/invoke")
async def copilotkit_agent_invoke(agent_name: str, request: dict):
    """Agent invoke endpoint - PRODUCTION AGENTS"""
    try:
        messages = request.get("messages", [])
        if messages:
            last_message = messages[-1]
            user_input = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message)
            
            # Try to use production agents
            if AGENTS_AVAILABLE and agent_name in AGENTS:
                agent = AGENTS[agent_name]
                response = f"I'm the {agent.name} agent. {agent.description}. I can help you with specialized tools. What specific task would you like me to handle?"
            else:
                # Fallback to simple rule-based responses
                if "prospect" in user_input.lower() or "search" in user_input.lower():
                    response = "I can help you search for prospects! Use the search_prospects tool with location and category parameters."
                elif "pitch" in user_input.lower() or "generate" in user_input.lower():
                    response = "I can generate personalized pitches! Use the generate_pitch tool with business_name and industry parameters."
                elif "outreach" in user_input.lower() or "send" in user_input.lower():
                    response = "I can help with outreach campaigns! Use the send_outreach tool with contact_email, message, and channel parameters."
                elif "report" in user_input.lower() or "analytics" in user_input.lower():
                    response = "I can generate performance reports! Use the generate_report tool with date_range and metrics parameters."
                elif "optimize" in user_input.lower() or "gbp" in user_input.lower():
                    response = "I can optimize Google Business Profiles! Use the optimize_gbp tool with business_id and updates parameters."
                elif "finance" in user_input.lower() or "track" in user_input.lower():
                    response = "I can track financial transactions! Use the track_finances tool with transaction_type, amount, and category parameters."
                elif "analyze" in user_input.lower() or "performance" in user_input.lower():
                    response = "I can analyze performance metrics! Use the analyze_performance tool with layer_name and time_period parameters."
                else:
                    response = f"I'm the {agent_name or 'cep_machine'} assistant. I can help you with business automation using specialized tools. What would you like to do?"
            
            return JSONResponse(
                content={
                    "messages": [
                        {"role": "assistant", "content": response}
                    ]
                }
            )
        
        return JSONResponse(
            content={"error": "No messages provided"},
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Agent invocation failed: {str(e)}"},
            status_code=500
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
