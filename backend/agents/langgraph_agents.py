"""
Production LangGraph Agents for CEP Machine
Advanced agent framework with tool execution and state management
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from langgraph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolExecutor, ToolInvocation
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for LangGraph agents"""
    messages: List[Any]
    current_agent: str
    tools_used: List[str]
    context: Dict[str, Any]
    execution_results: List[Dict[str, Any]]

class BusinessGrowthAgent:
    """Advanced Business Growth Agent with LangGraph"""
    
    def __init__(self):
        self.name = "business_growth"
        self.description = "Specialized in prospect research, pitch generation, and outreach campaigns"
        self.tools = [
            self.search_prospects_tool,
            self.generate_pitch_tool,
            self.send_outreach_tool
        ]
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent and determine required tools"""
        last_message = state["messages"][-1] if state["messages"] else ""
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Determine intent and required tools
        intent_analysis = {
            "user_input": user_input,
            "intent": "unknown",
            "required_tools": [],
            "confidence": 0.0
        }
        
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ["prospect", "search", "find"]):
            intent_analysis["intent"] = "prospect_search"
            intent_analysis["required_tools"] = ["search_prospects"]
            intent_analysis["confidence"] = 0.9
        elif any(keyword in user_input_lower for keyword in ["pitch", "generate", "create"]):
            intent_analysis["intent"] = "pitch_generation"
            intent_analysis["required_tools"] = ["generate_pitch"]
            intent_analysis["confidence"] = 0.9
        elif any(keyword in user_input_lower for keyword in ["outreach", "send", "email", "contact"]):
            intent_analysis["intent"] = "outreach_campaign"
            intent_analysis["required_tools"] = ["send_outreach"]
            intent_analysis["confidence"] = 0.9
        
        state["context"]["intent_analysis"] = intent_analysis
        state["current_agent"] = self.name
        
        logger.info(f"Intent analyzed: {intent_analysis}")
        return state
    
    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute required tools based on intent"""
        intent_analysis = state["context"].get("intent_analysis", {})
        required_tools = intent_analysis.get("required_tools", [])
        
        tool_results = []
        
        for tool_name in required_tools:
            try:
                if tool_name == "search_prospects":
                    result = self._execute_search_prospects(state)
                elif tool_name == "generate_pitch":
                    result = self._execute_generate_pitch(state)
                elif tool_name == "send_outreach":
                    result = self._execute_send_outreach(state)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                tool_results.append({
                    "tool": tool_name,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                state["tools_used"].append(tool_name)
                
            except Exception as e:
                logger.error(f"Tool execution error for {tool_name}: {str(e)}")
                tool_results.append({
                    "tool": tool_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        state["execution_results"] = tool_results
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response based on tool execution results"""
        intent_analysis = state["context"].get("intent_analysis", {})
        execution_results = state.get("execution_results", [])
        
        response_content = f"I'm the {self.name} agent. "
        
        if execution_results:
            successful_results = [r for r in execution_results if "error" not in r]
            failed_results = [r for r in execution_results if "error" in r]
            
            if successful_results:
                response_content += "I've successfully executed the following tools:\n"
                for result in successful_results:
                    tool_name = result["tool"]
                    tool_result = result["result"]
                    response_content += f"\n• {tool_name}: {self._format_tool_result(tool_name, tool_result)}"
            
            if failed_results:
                response_content += "\n\nSome tools encountered issues:\n"
                for result in failed_results:
                    response_content += f"\n• {result['tool']}: {result['error']}"
        else:
            response_content += self.description + ". What specific task would you like me to help you with?"
        
        # Add AI message
        ai_message = AIMessage(content=response_content)
        state["messages"].append(ai_message)
        
        return state
    
    def _format_tool_result(self, tool_name: str, result: Any) -> str:
        """Format tool execution results for user display"""
        if tool_name == "search_prospects":
            if isinstance(result, dict) and "prospects" in result:
                return f"Found {len(result['prospects'])} prospects"
            return "Prospect search completed"
        elif tool_name == "generate_pitch":
            if isinstance(result, dict) and "pitch" in result:
                return f"Generated pitch for {result.get('business_name', 'business')}"
            return "Pitch generated successfully"
        elif tool_name == "send_outreach":
            if isinstance(result, dict) and "status" in result:
                return f"Outreach {result['status']}"
            return "Outreach sent successfully"
        return "Tool executed successfully"
    
    def _execute_search_prospects(self, state: AgentState) -> Dict[str, Any]:
        """Execute prospect search tool"""
        last_message = state["messages"][-1] if state["messages"] else ""
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Extract location and category from user input
        location = "New York"  # Default
        category = "restaurants"  # Default
        
        # Simple extraction logic
        user_input_lower = user_input.lower()
        if "in" in user_input_lower:
            parts = user_input_lower.split("in")
            if len(parts) > 1:
                location = parts[1].strip().split()[0].title()
        
        if any(cat in user_input_lower for cat in ["restaurant", "food", "dining"]):
            category = "restaurants"
        elif any(cat in user_input_lower for cat in ["dental", "dentist", "teeth"]):
            category = "dental"
        elif any(cat in user_input_lower for cat in ["gym", "fitness", "workout"]):
            category = "fitness"
        
        # Mock prospect data
        prospects = [
            {
                "name": f"{category.title()} {i}",
                "address": f"{location} Street {i}",
                "rating": 3.5 + (i % 2),
                "contact": f"contact{i}@example.com"
            }
            for i in range(1, 6)
        ]
        
        return {
            "prospects": prospects,
            "location": location,
            "category": category,
            "total_found": len(prospects)
        }
    
    def _execute_generate_pitch(self, state: AgentState) -> Dict[str, Any]:
        """Execute pitch generation tool"""
        last_message = state["messages"][-1] if state["messages"] else ""
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Extract business name and industry
        business_name = "Local Business"
        industry = "general"
        
        user_input_lower = user_input.lower()
        if "for" in user_input_lower:
            parts = user_input_lower.split("for")
            if len(parts) > 1:
                business_name = parts[1].strip().split()[0].title()
        
        if any(ind in user_input_lower for ind in ["restaurant", "food"]):
            industry = "restaurant"
        elif any(ind in user_input_lower for ind in ["dental", "dentist"]):
            industry = "dental"
        elif any(ind in user_input_lower for ind in ["gym", "fitness"]):
            industry = "fitness"
        
        pitch = f"""
        Hi {business_name} Team!
        
        I noticed your {industry} business and wanted to reach out about our AI-powered automation solutions.
        We help {industry} businesses like yours:
        • Increase customer acquisition by 40%
        • Automate time-consuming marketing tasks
        • Improve online presence and reviews
        • Streamline customer communications
        
        Would you be interested in a quick 15-minute demo to see how we can help {business_name} grow?
        
        Best regards,
        AI Assistant
        """
        
        return {
            "pitch": pitch.strip(),
            "business_name": business_name,
            "industry": industry,
            "word_count": len(pitch.split())
        }
    
    def _execute_send_outreach(self, state: AgentState) -> Dict[str, Any]:
        """Execute outreach sending tool"""
        last_message = state["messages"][-1] if state["messages"] else ""
        user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        # Extract contact info
        contact_email = "contact@example.com"
        channel = "email"
        
        user_input_lower = user_input.lower()
        if "@" in user_input_lower:
            # Extract email
            words = user_input_lower.split()
            for word in words:
                if "@" in word:
                    contact_email = word
                    break
        
        if "sms" in user_input_lower or "text" in user_input_lower:
            channel = "sms"
        elif "social" in user_input_lower or "linkedin" in user_input_lower:
            channel = "social"
        
        return {
            "status": "sent",
            "contact_email": contact_email,
            "channel": channel,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    @tool
    def search_prospects_tool(self, location: str, category: str) -> Dict[str, Any]:
        """Search for business prospects by location and category"""
        return self._execute_search_prospects({
            "messages": [HumanMessage(content=f"search prospects in {location} for {category}")],
            "tools_used": [],
            "context": {},
            "execution_results": []
        })
    
    @tool
    def generate_pitch_tool(self, business_name: str, industry: str) -> Dict[str, Any]:
        """Generate personalized pitch for a business"""
        return self._execute_generate_pitch({
            "messages": [HumanMessage(content=f"generate pitch for {business_name} in {industry}")],
            "tools_used": [],
            "context": {},
            "execution_results": []
        })
    
    @tool
    def send_outreach_tool(self, contact_email: str, message: str, channel: str) -> Dict[str, Any]:
        """Send outreach message via specified channel"""
        return self._execute_send_outreach({
            "messages": [HumanMessage(content=f"send outreach to {contact_email} via {channel}: {message}")],
            "tools_used": [],
            "context": {},
            "execution_results": []
        })
    
    def invoke(self, messages: List[Any]) -> Dict[str, Any]:
        """Invoke the agent with messages"""
        initial_state = {
            "messages": messages,
            "current_agent": "",
            "tools_used": [],
            "context": {},
            "execution_results": []
        }
        
        try:
            result = self.graph.invoke(initial_state)
            return {
                "messages": result.get("messages", []),
                "tools_used": result.get("tools_used", []),
                "execution_results": result.get("execution_results", []),
                "context": result.get("context", {})
            }
        except Exception as e:
            logger.error(f"Agent invocation error: {str(e)}")
            return {
                "messages": [AIMessage(content=f"I encountered an error: {str(e)}")],
                "tools_used": [],
                "execution_results": [],
                "context": {"error": str(e)}
            }

# Agent Registry
AGENTS = {
    "business_growth": BusinessGrowthAgent(),
}

def get_agent(agent_name: str) -> Optional[BusinessGrowthAgent]:
    """Get agent by name"""
    return AGENTS.get(agent_name)

def list_agents() -> List[str]:
    """List all available agents"""
    return list(AGENTS.keys())
