"""
Production CopilotKit Agents for CEP Machine
Built with LangGraph for complex agent workflows
"""

from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from copilotkit.langgraph import LangGraphAgent, CopilotKitConfig
import json
import asyncio
from datetime import datetime

class CEPAgentState:
    """State for CEP Machine agents"""
    messages: List[BaseMessage]
    current_task: Optional[str]
    business_context: Optional[Dict[str, Any]]
    actions_taken: List[Dict[str, Any]]
    next_steps: List[str]

# CEP Machine Tools
@tool
def analyze_performance(layer_name: str, time_period: str) -> Dict[str, Any]:
    """Analyze performance metrics for a specific layer"""
    return {
        "layer": layer_name,
        "period": time_period,
        "metrics": {
            "conversion_rate": "3.2%",
            "avg_response_time": "1.2s",
            "error_rate": "0.1%",
            "throughput": "1000 req/min"
        },
        "recommendations": [
            "Optimize database queries",
            "Implement caching layer",
            "Scale horizontally"
        ]
    }

@tool
def search_prospects(location: str, category: str) -> List[Dict[str, Any]]:
    """Search for business prospects by location and category"""
    return [
        {
            "name": "Tech Startup Inc",
            "location": location,
            "category": category,
            "revenue": "$5M",
            "employees": 50,
            "contact": "ceo@techstartup.com"
        },
        {
            "name": "Local Business Co",
            "location": location,
            "category": category,
            "revenue": "$2M",
            "employees": 25,
            "contact": "owner@localbusiness.com"
        }
    ]

@tool
def generate_pitch(business_name: str, industry: str) -> Dict[str, Any]:
    """Generate personalized outreach content"""
    return {
        "subject": f"Partnership Opportunity with {business_name}",
        "body": f"Hi {business_name} team, We noticed your innovative work in {industry}...",
        "call_to_action": "Schedule a 15-minute demo",
        "personalization_score": 0.85
    }

@tool
def optimize_gbp(business_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize Google Business Profile"""
    return {
        "business_id": business_id,
        "updates_applied": updates,
        "impact": {
            "visibility_boost": "+45%",
            "engagement_increase": "+32%",
            "ranking_improvement": "+28%"
        }
    }

@tool
def send_outreach(contact_email: str, message: str, channel: str) -> Dict[str, Any]:
    """Send outreach messages"""
    return {
        "status": "sent",
        "recipient": contact_email,
        "channel": channel,
        "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "delivery_status": "delivered"
    }

@tool
def track_finances(amount: float, category: str, transaction_type: str) -> Dict[str, Any]:
    """Track financial transactions"""
    return {
        "transaction_id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "amount": amount,
        "category": category,
        "type": transaction_type,
        "timestamp": datetime.now().isoformat(),
        "status": "recorded"
    }

# Agent Workflows

def create_performance_analyzer_agent() -> LangGraphAgent:
    """Agent for analyzing CEP Machine performance"""
    
    def merge_state(state: CEPAgentState, messages: List[BaseMessage], actions: List[Any], agent_name: str) -> CEPAgentState:
        """Custom state merging for performance analyzer"""
        new_state = CEPAgentState()
        new_state.messages = state.messages + messages
        new_state.current_task = state.current_task or "performance_analysis"
        new_state.business_context = state.business_context or {}
        new_state.actions_taken = state.actions_taken + [{"action": str(action), "timestamp": datetime.now().isoformat()} for action in actions]
        new_state.next_steps = []
        return new_state
    
    def convert_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
        """Convert messages for LangChain compatibility"""
        return messages
    
    # Build the graph
    workflow = StateGraph(CEPAgentState)
    
    def analyze_node(state: CEPAgentState) -> CEPAgentState:
        """Main analysis node"""
        last_message = state.messages[-1] if state.messages else None
        
        if last_message and isinstance(last_message, HumanMessage):
            # Extract layer and time period from message
            content = last_message.content.lower()
            layer = "unknown"
            period = "last_7_days"
            
            # Simple parsing - in production, use NLP
            if "layer" in content:
                words = content.split()
                for i, word in enumerate(words):
                    if word == "layer" and i + 1 < len(words):
                        layer = words[i + 1]
                        break
            
            if "week" in content:
                period = "last_7_days"
            elif "month" in content:
                period = "last_30_days"
            
            # Use the analysis tool
            result = analyze_performance(layer, period)
            
            state.messages.append(AIMessage(
                content=f"Performance analysis for {layer} over {period}:\n\n"
                f"Conversion Rate: {result['metrics']['conversion_rate']}\n"
                f"Response Time: {result['metrics']['avg_response_time']}\n"
                f"Error Rate: {result['metrics']['error_rate']}\n"
                f"Throughput: {result['metrics']['throughput']}\n\n"
                f"Recommendations:\n" + "\n".join(f"- {rec}" for rec in result['recommendations'])
            ))
            
            state.actions_taken.append({"tool": "analyze_performance", "result": result})
        
        return state
    
    workflow.add_node("analyze", analyze_node)
    workflow.set_entry_point("analyze")
    workflow.set_finish_point("analyze")
    
    # Compile the graph
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    # Create CopilotKit config
    config = CopilotKitConfig(
        merge_state=merge_state,
        convert_messages=convert_messages
    )
    
    return LangGraphAgent(
        name="performance_analyzer",
        description="Analyzes CEP Machine performance metrics and provides optimization recommendations",
        graph=graph,
        copilotkit_config=config
    )

def create_business_growth_agent() -> LangGraphAgent:
    """Agent for business growth and prospecting"""
    
    def merge_state(state: CEPAgentState, messages: List[BaseMessage], actions: List[Any], agent_name: str) -> CEPAgentState:
        """Custom state merging for business growth"""
        new_state = CEPAgentState()
        new_state.messages = state.messages + messages
        new_state.current_task = state.current_task or "business_growth"
        new_state.business_context = state.business_context or {}
        new_state.actions_taken = state.actions_taken + [{"action": str(action), "timestamp": datetime.now().isoformat()} for action in actions]
        new_state.next_steps = []
        return new_state
    
    def convert_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
        """Convert messages for LangChain compatibility"""
        return messages
    
    # Build the graph
    workflow = StateGraph(CEPAgentState)
    
    def prospect_node(state: CEPAgentState) -> CEPAgentState:
        """Find and analyze prospects"""
        last_message = state.messages[-1] if state.messages else None
        
        if last_message and isinstance(last_message, HumanMessage):
            content = last_message.content.lower()
            
            # Extract location and category
            location = "san_francisco"  # default
            category = "technology"  # default
            
            if "in" in content:
                words = content.split()
                for i, word in enumerate(words):
                    if word == "in" and i + 1 < len(words):
                        location = words[i + 1].replace(",", "")
                        break
            
            # Find prospects
            prospects = search_prospects(location, category)
            
            response = f"Found {len(prospects)} prospects in {location}:\n\n"
            for prospect in prospects:
                response += f"📊 {prospect['name']}\n"
                response += f"   Revenue: {prospect['revenue']}\n"
                response += f"   Employees: {prospect['employees']}\n"
                response += f"   Contact: {prospect['contact']}\n\n"
            
            state.messages.append(AIMessage(content=response))
            state.actions_taken.append({"tool": "search_prospects", "count": len(prospects)})
            state.business_context = {"prospects": prospects, "location": location, "category": category}
        
        return state
    
    def outreach_node(state: CEPAgentState) -> CEPAgentState:
        """Generate and send outreach"""
        if state.business_context and "prospects" in state.business_context:
            prospects = state.business_context["prospects"]
            
            outreach_results = []
            for prospect in prospects[:2]:  # Limit to 2 for demo
                # Generate pitch
                pitch = generate_pitch(prospect["name"], prospect.get("category", "business"))
                
                # Send outreach
                result = send_outreach(prospect["contact"], pitch["body"], "email")
                outreach_results.append(result)
            
            response = f"📧 Outreach sent to {len(outreach_results)} prospects:\n\n"
            for result in outreach_results:
                response += f"✅ Message ID: {result['message_id']}\n"
                response += f"   Status: {result['status']}\n\n"
            
            state.messages.append(AIMessage(content=response))
            state.actions_taken.append({"tool": "send_outreach", "results": outreach_results})
        
        return state
    
    workflow.add_node("prospect", prospect_node)
    workflow.add_node("outreach", outreach_node)
    workflow.add_edge("prospect", "outreach")
    workflow.set_entry_point("prospect")
    workflow.set_finish_point("outreach")
    
    # Compile the graph
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    # Create CopilotKit config
    config = CopilotKitConfig(
        merge_state=merge_state,
        convert_messages=convert_messages
    )
    
    return LangGraphAgent(
        name="business_growth",
        description="Finds business prospects and generates personalized outreach campaigns",
        graph=graph,
        copilotkit_config=config
    )

def create_finance_agent() -> LangGraphAgent:
    """Agent for financial tracking and analysis"""
    
    def merge_state(state: CEPAgentState, messages: List[BaseMessage], actions: List[Any], agent_name: str) -> CEPAgentState:
        """Custom state merging for finance tracking"""
        new_state = CEPAgentState()
        new_state.messages = state.messages + messages
        new_state.current_task = state.current_task or "finance_tracking"
        new_state.business_context = state.business_context or {}
        new_state.actions_taken = state.actions_taken + [{"action": str(action), "timestamp": datetime.now().isoformat()} for action in actions]
        new_state.next_steps = []
        return new_state
    
    def convert_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
        """Convert messages for LangChain compatibility"""
        return messages
    
    # Build the graph
    workflow = StateGraph(CEPAgentState)
    
    def track_node(state: CEPAgentState) -> CEPAgentState:
        """Track financial transactions"""
        last_message = state.messages[-1] if state.messages else None
        
        if last_message and isinstance(last_message, HumanMessage):
            content = last_message.content.lower()
            
            # Simple parsing for financial data
            amount = 0.0
            category = "general"
            transaction_type = "income"
            
            # Look for numbers in the message
            import re
            numbers = re.findall(r'\$?(\d+(?:\.\d+)?)', content)
            if numbers:
                amount = float(numbers[0])
            
            if "expense" in content or "spent" in content:
                transaction_type = "expense"
            
            if "revenue" in content or "income" in content:
                category = "revenue"
            elif "marketing" in content:
                category = "marketing"
            elif "operations" in content:
                category = "operations"
            
            # Track the transaction
            result = track_finances(amount, category, transaction_type)
            
            response = f"💰 Transaction recorded:\n\n"
            response += f"Amount: ${amount}\n"
            response += f"Category: {category}\n"
            response += f"Type: {transaction_type}\n"
            response += f"Transaction ID: {result['transaction_id']}\n"
            response += f"Status: {result['status']}\n"
            
            state.messages.append(AIMessage(content=response))
            state.actions_taken.append({"tool": "track_finances", "result": result})
        
        return state
    
    workflow.add_node("track", track_node)
    workflow.set_entry_point("track")
    workflow.set_finish_point("track")
    
    # Compile the graph
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    # Create CopilotKit config
    config = CopilotKitConfig(
        merge_state=merge_state,
        convert_messages=convert_messages
    )
    
    return LangGraphAgent(
        name="finance_tracker",
        description="Tracks financial transactions and provides business insights",
        graph=graph,
        copilotkit_config=config
    )

# Agent Registry
AGENTS = {
    "performance_analyzer": create_performance_analyzer_agent(),
    "business_growth": create_business_growth_agent(),
    "finance_tracker": create_finance_agent()
}

def get_agent(agent_name: str) -> Optional[LangGraphAgent]:
    """Get an agent by name"""
    return AGENTS.get(agent_name)

def list_agents() -> List[str]:
    """List all available agents"""
    return list(AGENTS.keys())

if __name__ == "__main__":
    # Test the agents
    print("Available CEP Machine Agents:")
    for name in list_agents():
        agent = get_agent(name)
        print(f"- {name}: {agent.description}")
