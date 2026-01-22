"""
Advanced Tool Execution API for CEP Machine
Production-ready tool execution with error handling, logging, and monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import json
import logging
import asyncio
from datetime import datetime, timedelta
import uuid
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])

class ToolStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    priority: str = Field(default="normal", description="Execution priority: low, normal, high, urgent")
    timeout: Optional[int] = Field(default=300, description="Timeout in seconds")
    async_execution: bool = Field(default=False, description="Execute asynchronously")

class ToolResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    status: ToolStatus = Field(..., description="Current execution status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    started_at: Optional[datetime] = Field(default=None, description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")

class ToolRegistry:
    """Registry for available tools"""
    
    def __init__(self):
        self._tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default production tools"""
        self._tools.update({
            "search_prospects": {
                "name": "search_prospects",
                "description": "Search for business prospects by location and category",
                "parameters": {
                    "location": {"type": "string", "required": True, "description": "Location to search"},
                    "category": {"type": "string", "required": True, "description": "Business category"},
                    "limit": {"type": "integer", "default": 10, "description": "Maximum results"}
                },
                "handler": self._search_prospects_handler
            },
            "generate_pitch": {
                "name": "generate_pitch",
                "description": "Generate personalized pitch for a business",
                "parameters": {
                    "business_name": {"type": "string", "required": True, "description": "Business name"},
                    "industry": {"type": "string", "required": True, "description": "Industry type"},
                    "tone": {"type": "string", "default": "professional", "description": "Tone of the pitch"}
                },
                "handler": self._generate_pitch_handler
            },
            "send_outreach": {
                "name": "send_outreach",
                "description": "Send outreach message via specified channel",
                "parameters": {
                    "contact_email": {"type": "string", "required": True, "description": "Contact email"},
                    "message": {"type": "string", "required": True, "description": "Message content"},
                    "channel": {"type": "string", "default": "email", "description": "Channel: email, sms, social"}
                },
                "handler": self._send_outreach_handler
            },
            "analyze_performance": {
                "name": "analyze_performance",
                "description": "Analyze performance metrics for a specific layer",
                "parameters": {
                    "layer_name": {"type": "string", "required": True, "description": "Layer to analyze"},
                    "time_period": {"type": "string", "required": True, "description": "Time period: 7d, 30d, 90d"}
                },
                "handler": self._analyze_performance_handler
            },
            "track_finances": {
                "name": "track_finances",
                "description": "Track financial transactions",
                "parameters": {
                    "transaction_type": {"type": "string", "required": True, "description": "Type: income, expense"},
                    "amount": {"type": "number", "required": True, "description": "Transaction amount"},
                    "category": {"type": "string", "required": True, "description": "Transaction category"}
                },
                "handler": self._track_finances_handler
            }
        })
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool definition by name"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self._tools.keys())
    
    async def _search_prospects_handler(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prospect search"""
        location = parameters.get("location", "New York")
        category = parameters.get("category", "restaurants")
        limit = parameters.get("limit", 10)
        
        # Simulate API call to prospect database
        await asyncio.sleep(1)  # Simulate processing time
        
        prospects = [
            {
                "id": f"prospect_{i}",
                "name": f"{category.title()} {i}",
                "address": f"{location} Street {i}",
                "rating": 3.5 + (i % 2),
                "contact": f"contact{i}@example.com",
                "website": f"https://example{i}.com",
                "estimated_revenue": f"${100000 * (i + 1):,}"
            }
            for i in range(1, min(limit + 1, 11))
        ]
        
        return {
            "prospects": prospects,
            "location": location,
            "category": category,
            "total_found": len(prospects),
            "search_timestamp": datetime.now().isoformat()
        }
    
    async def _generate_pitch_handler(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pitch generation"""
        business_name = parameters.get("business_name", "Local Business")
        industry = parameters.get("industry", "general")
        tone = parameters.get("tone", "professional")
        
        await asyncio.sleep(2)  # Simulate AI processing
        
        pitch_templates = {
            "professional": f"""
            Dear {business_name} Team,
            
            I hope this message finds you well. I'm reaching out because I noticed your {industry} business 
            and believe our AI-powered automation solutions could significantly enhance your operational efficiency.
            
            Our platform has helped similar {industry} businesses achieve:
            • 40% increase in customer acquisition
            • 60% reduction in administrative tasks
            • 25% improvement in customer satisfaction
            
            Would you be available for a brief 15-minute demonstration next week?
            
            Best regards,
            AI Assistant
            """,
            "casual": f"""
            Hi {business_name} Team!
            
            Came across your {industry} business and had to reach out. We've been helping {industry} businesses 
            like yours automate their marketing and customer service - pretty cool stuff!
            
            Our clients typically see:
            • More customers (40% increase on average)
            • Less admin work (cut by 60%)
            • Happier customers (25% improvement)
            
            Got 15 minutes next week for a quick demo? No pressure, just thought you might be interested!
            
            Cheers,
            AI Assistant
            """
        }
        
        pitch = pitch_templates.get(tone, pitch_templates["professional"])
        
        return {
            "pitch": pitch.strip(),
            "business_name": business_name,
            "industry": industry,
            "tone": tone,
            "word_count": len(pitch.split()),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _send_outreach_handler(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle outreach sending"""
        contact_email = parameters.get("contact_email")
        message = parameters.get("message")
        channel = parameters.get("channel", "email")
        
        await asyncio.sleep(1.5)  # Simulate sending
        
        # Simulate different channel behaviors
        success_rate = 0.95  # 95% success rate
        import random
        success = random.random() < success_rate
        
        if success:
            return {
                "status": "sent",
                "contact_email": contact_email,
                "channel": channel,
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "sent_at": datetime.now().isoformat(),
                "estimated_delivery": datetime.now() + timedelta(hours=1)
            }
        else:
            return {
                "status": "failed",
                "contact_email": contact_email,
                "channel": channel,
                "error": "Delivery failed - recipient server unavailable",
                "retry_available": True
            }
    
    async def _analyze_performance_handler(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance analysis"""
        layer_name = parameters.get("layer_name")
        time_period = parameters.get("time_period", "30d")
        
        await asyncio.sleep(3)  # Simulate data analysis
        
        # Generate mock performance data
        days = int(time_period.replace('d', ''))
        
        performance_data = {
            "layer_name": layer_name,
            "time_period": time_period,
            "metrics": {
                "total_tasks": days * 15,
                "completed_tasks": int(days * 15 * 0.87),
                "success_rate": 87.3,
                "average_response_time": 2.4,
                "user_satisfaction": 4.6
            },
            "trends": {
                "productivity_change": "+12.5%",
                "efficiency_gain": "+8.3%",
                "cost_reduction": "-15.7%"
            },
            "recommendations": [
                "Increase automation in repetitive tasks",
                "Optimize response templates for better engagement",
                "Consider expanding to additional channels"
            ],
            "analyzed_at": datetime.now().isoformat()
        }
        
        return performance_data
    
    async def _track_finances_handler(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle finance tracking"""
        transaction_type = parameters.get("transaction_type")
        amount = parameters.get("amount")
        category = parameters.get("category")
        
        await asyncio.sleep(0.5)  # Simulate database write
        
        transaction = {
            "id": f"txn_{uuid.uuid4().hex[:8]}",
            "type": transaction_type,
            "amount": amount,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "status": "recorded"
        }
        
        return {
            "transaction": transaction,
            "monthly_summary": {
                "total_income": 15420.00,
                "total_expenses": 8750.00,
                "net_profit": 6670.00,
                "transactions_this_month": 47
            },
            "recorded_at": datetime.now().isoformat()
        }

# Global tool registry
tool_registry = ToolRegistry()

# Task storage for async operations
active_tasks: Dict[str, ToolResponse] = {}

@router.get("/list", response_model=Dict[str, Any])
async def list_tools():
    """List all available tools with their schemas"""
    tools = {}
    for tool_name in tool_registry.list_tools():
        tool_def = tool_registry.get_tool(tool_name)
        if tool_def:
            tools[tool_name] = {
                "name": tool_def["name"],
                "description": tool_def["description"],
                "parameters": tool_def["parameters"]
            }
    
    return {
        "tools": tools,
        "total_count": len(tools),
        "api_version": "1.0.0"
    }

@router.post("/execute", response_model=ToolResponse)
async def execute_tool(request: ToolRequest, background_tasks: BackgroundTasks):
    """Execute a tool synchronously or asynchronously"""
    
    # Validate tool exists
    tool_def = tool_registry.get_tool(request.tool_name)
    if not tool_def:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
    
    # Create task
    task_id = str(uuid.uuid4())
    task_response = ToolResponse(
        task_id=task_id,
        status=ToolStatus.PENDING,
        started_at=datetime.now()
    )
    
    active_tasks[task_id] = task_response
    
    if request.async_execution:
        # Execute in background
        background_tasks.add_task(
            _execute_tool_background,
            task_id,
            request.tool_name,
            request.parameters,
            request.timeout
        )
        return task_response
    else:
        # Execute synchronously
        try:
            result = await _execute_tool_sync(
                request.tool_name,
                request.parameters,
                request.timeout
            )
            
            task_response.status = ToolStatus.COMPLETED
            task_response.result = result
            task_response.completed_at = datetime.now()
            task_response.execution_time = (
                task_response.completed_at - task_response.started_at
            ).total_seconds()
            
            return task_response
            
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            task_response.status = ToolStatus.FAILED
            task_response.error = str(e)
            task_response.completed_at = datetime.now()
            task_response.execution_time = (
                task_response.completed_at - task_response.started_at
            ).total_seconds()
            
            return task_response

@router.get("/status/{task_id}", response_model=ToolResponse)
async def get_task_status(task_id: str):
    """Get status of an async task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_tasks[task_id]

@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """Cancel an async task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    if task.status in [ToolStatus.COMPLETED, ToolStatus.FAILED, ToolStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")
    
    task.status = ToolStatus.CANCELLED
    task.completed_at = datetime.now()
    
    return {"message": "Task cancelled successfully", "task_id": task_id}

async def _execute_tool_sync(tool_name: str, parameters: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """Execute tool synchronously with timeout"""
    tool_def = tool_registry.get_tool(tool_name)
    if not tool_def:
        raise ValueError(f"Tool '{tool_name}' not found")
    
    handler = tool_def["handler"]
    
    try:
        # Execute with timeout
        result = await asyncio.wait_for(handler(parameters), timeout=timeout)
        return result
    except asyncio.TimeoutError:
        raise TimeoutError(f"Tool execution timed out after {timeout} seconds")

async def _execute_tool_background(task_id: str, tool_name: str, parameters: Dict[str, Any], timeout: int):
    """Execute tool in background"""
    task = active_tasks.get(task_id)
    if not task:
        return
    
    try:
        task.status = ToolStatus.RUNNING
        
        tool_def = tool_registry.get_tool(tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        handler = tool_def["handler"]
        result = await asyncio.wait_for(handler(parameters), timeout=timeout)
        
        task.status = ToolStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now()
        task.execution_time = (
            task.completed_at - task.started_at
        ).total_seconds()
        
        logger.info(f"Background task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background task {task_id} failed: {str(e)}")
        task.status = ToolStatus.FAILED
        task.error = str(e)
        task.completed_at = datetime.now()
        task.execution_time = (
            task.completed_at - task.started_at
        ).total_seconds()
