"""
Multi-Agent Orchestrator for CEP Machine
Production-ready agent coordination and workflow management
"""

from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class OrchestratorState(TypedDict):
    """State for the orchestrator workflow"""
    messages: List[Any]
    user_input: str
    required_agents: List[str]
    agent_results: Dict[str, Any]
    merged_results: List[Dict[str, Any]]
    current_agent: Optional[str]
    execution_order: List[str]
    errors: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class AgentOrchestrator:
    """
    Multi-agent orchestrator that coordinates multiple specialized agents
    to handle complex user requests.
    """
    
    def __init__(self):
        self.agents = {}
        self._load_agents()
        self.workflow = self._build_workflow()
    
    def _load_agents(self):
        """Load available agents"""
        try:
            from backend.agents.langgraph_agents import BusinessGrowthAgent, AGENTS
            self.agents = AGENTS.copy()
            logger.info(f"Loaded {len(self.agents)} agents")
        except ImportError as e:
            logger.warning(f"Could not load agents: {e}")
            self.agents = {}
    
    def _build_workflow(self) -> StateGraph:
        """Build the orchestration workflow"""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("plan_execution", self._plan_execution)
        workflow.add_node("execute_agents", self._execute_agents)
        workflow.add_node("merge_results", self._merge_results)
        workflow.add_node("generate_response", self._generate_response)
        
        # Set entry point
        workflow.set_entry_point("analyze_intent")
        
        # Add edges
        workflow.add_edge("analyze_intent", "plan_execution")
        workflow.add_edge("plan_execution", "execute_agents")
        workflow.add_edge("execute_agents", "merge_results")
        workflow.add_edge("merge_results", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _analyze_intent(self, state: OrchestratorState) -> OrchestratorState:
        """Analyze user intent and determine required agents"""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        if last_message:
            user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            user_input = state.get("user_input", "")
        
        state["user_input"] = user_input
        user_input_lower = user_input.lower()
        
        # Determine required agents based on intent
        required_agents = []
        
        # Business growth related
        if any(keyword in user_input_lower for keyword in [
            "prospect", "search", "find", "business", "lead", "company"
        ]):
            required_agents.append("business_growth")
        
        # Pitch generation
        if any(keyword in user_input_lower for keyword in [
            "pitch", "generate", "create", "write", "compose", "draft"
        ]):
            required_agents.append("business_growth")
        
        # Outreach
        if any(keyword in user_input_lower for keyword in [
            "outreach", "send", "email", "contact", "reach out", "message"
        ]):
            required_agents.append("business_growth")
        
        # Performance analysis
        if any(keyword in user_input_lower for keyword in [
            "analyze", "performance", "report", "analytics", "metrics", "stats"
        ]):
            if "performance_analyzer" in self.agents:
                required_agents.append("performance_analyzer")
            else:
                required_agents.append("business_growth")
        
        # Finance tracking
        if any(keyword in user_input_lower for keyword in [
            "finance", "track", "expense", "revenue", "money", "payment", "invoice"
        ]):
            if "finance_tracker" in self.agents:
                required_agents.append("finance_tracker")
            else:
                required_agents.append("business_growth")
        
        # Default to business_growth if no specific agent matched
        if not required_agents and self.agents:
            required_agents.append(list(self.agents.keys())[0])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_agents = []
        for agent in required_agents:
            if agent not in seen and agent in self.agents:
                seen.add(agent)
                unique_agents.append(agent)
        
        state["required_agents"] = unique_agents
        state["metadata"] = {
            "intent_analyzed_at": datetime.utcnow().isoformat(),
            "detected_intents": required_agents
        }
        
        logger.info(f"Intent analysis complete. Required agents: {unique_agents}")
        return state
    
    def _plan_execution(self, state: OrchestratorState) -> OrchestratorState:
        """Plan the execution order of agents"""
        required_agents = state.get("required_agents", [])
        
        # Define agent dependencies and priorities
        agent_priorities = {
            "business_growth": 1,
            "performance_analyzer": 2,
            "finance_tracker": 3
        }
        
        # Sort agents by priority
        execution_order = sorted(
            required_agents,
            key=lambda x: agent_priorities.get(x, 99)
        )
        
        state["execution_order"] = execution_order
        state["agent_results"] = {}
        state["errors"] = []
        
        logger.info(f"Execution plan: {execution_order}")
        return state
    
    def _execute_agents(self, state: OrchestratorState) -> OrchestratorState:
        """Execute agents in planned order"""
        execution_order = state.get("execution_order", [])
        messages = state.get("messages", [])
        agent_results = state.get("agent_results", {})
        errors = state.get("errors", [])
        
        for agent_name in execution_order:
            state["current_agent"] = agent_name
            
            if agent_name not in self.agents:
                errors.append({
                    "agent": agent_name,
                    "error": f"Agent '{agent_name}' not found",
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            
            try:
                agent = self.agents[agent_name]
                
                # Invoke agent
                result = agent.invoke(messages)
                
                agent_results[agent_name] = {
                    "success": True,
                    "result": result,
                    "executed_at": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Agent '{agent_name}' executed successfully")
                
            except Exception as e:
                error_info = {
                    "agent": agent_name,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                errors.append(error_info)
                agent_results[agent_name] = {
                    "success": False,
                    "error": str(e),
                    "executed_at": datetime.utcnow().isoformat()
                }
                logger.error(f"Agent '{agent_name}' failed: {str(e)}")
        
        state["agent_results"] = agent_results
        state["errors"] = errors
        state["current_agent"] = None
        
        return state
    
    def _merge_results(self, state: OrchestratorState) -> OrchestratorState:
        """Merge results from all executed agents"""
        agent_results = state.get("agent_results", {})
        merged_results = []
        
        for agent_name, result_data in agent_results.items():
            if result_data.get("success"):
                result = result_data.get("result", {})
                
                # Extract messages from agent result
                if isinstance(result, dict):
                    messages = result.get("messages", [])
                    execution_results = result.get("execution_results", [])
                    
                    merged_results.append({
                        "agent": agent_name,
                        "messages": messages,
                        "execution_results": execution_results,
                        "tools_used": result.get("tools_used", []),
                        "context": result.get("context", {})
                    })
        
        state["merged_results"] = merged_results
        
        logger.info(f"Merged results from {len(merged_results)} agents")
        return state
    
    def _generate_response(self, state: OrchestratorState) -> OrchestratorState:
        """Generate final response from merged results"""
        merged_results = state.get("merged_results", [])
        errors = state.get("errors", [])
        user_input = state.get("user_input", "")
        
        response_parts = []
        
        # Add successful agent responses
        for result in merged_results:
            agent_name = result.get("agent", "unknown")
            messages = result.get("messages", [])
            
            for msg in messages:
                if hasattr(msg, 'content') and msg.type == "ai":
                    response_parts.append(msg.content)
        
        # If no responses, generate a fallback
        if not response_parts:
            if errors:
                error_messages = [e.get("error", "Unknown error") for e in errors]
                response_content = f"I encountered some issues while processing your request: {'; '.join(error_messages)}. Please try again or rephrase your request."
            else:
                response_content = f"I'm the CEP Machine orchestrator. I can help you with business automation tasks including prospect research, pitch generation, outreach campaigns, performance analysis, and finance tracking. How can I assist you today?"
        else:
            response_content = "\n\n".join(response_parts)
        
        # Add final AI message
        final_message = AIMessage(content=response_content)
        messages = state.get("messages", [])
        messages.append(final_message)
        state["messages"] = messages
        
        # Update metadata
        metadata = state.get("metadata", {})
        metadata["response_generated_at"] = datetime.utcnow().isoformat()
        metadata["agents_executed"] = list(state.get("agent_results", {}).keys())
        metadata["total_errors"] = len(errors)
        state["metadata"] = metadata
        
        return state
    
    def invoke(self, messages: List[Any]) -> Dict[str, Any]:
        """Invoke the orchestrator with messages"""
        initial_state: OrchestratorState = {
            "messages": messages,
            "user_input": "",
            "required_agents": [],
            "agent_results": {},
            "merged_results": [],
            "current_agent": None,
            "execution_order": [],
            "errors": [],
            "metadata": {}
        }
        
        try:
            result = self.workflow.invoke(initial_state)
            
            return {
                "messages": result.get("messages", []),
                "agent_results": result.get("agent_results", {}),
                "merged_results": result.get("merged_results", []),
                "errors": result.get("errors", []),
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Orchestrator invocation failed: {str(e)}")
            return {
                "messages": [AIMessage(content=f"I encountered an error: {str(e)}")],
                "agent_results": {},
                "merged_results": [],
                "errors": [{"error": str(e), "timestamp": datetime.utcnow().isoformat()}],
                "metadata": {"error": str(e)}
            }
    
    async def ainvoke(self, messages: List[Any]) -> Dict[str, Any]:
        """Async invoke the orchestrator"""
        return await asyncio.to_thread(self.invoke, messages)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents"""
        agents_info = []
        for name, agent in self.agents.items():
            agents_info.append({
                "name": name,
                "description": getattr(agent, 'description', 'No description'),
                "tools": getattr(agent, 'tools', [])
            })
        return agents_info
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get a specific agent by name"""
        return self.agents.get(agent_name)
    
    def register_agent(self, name: str, agent: Any):
        """Register a new agent"""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent"""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Unregistered agent: {name}")
            return True
        return False

# Global orchestrator instance
orchestrator = AgentOrchestrator()
