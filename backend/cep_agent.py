from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
import os
from typing import Dict, Any

class CEPState(MessagesState):
    """CEP Machine state with additional context"""
    current_layer: str = ""
    action: str = ""

async def cep_llm(state: CEPState):
    """CEP Machine LLM handler"""
    # Get OpenAI API key from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {"messages": [AIMessage(content="OpenAI API key not configured. Please set OPENAI_API_KEY in backend/.env")]}
    
    model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
    
    # System prompt for CEP Machine
    system_content = """You are a CEP Machine assistant - a 9-layer AI agent framework for business automation.

Available Layers:
1. Prospect Research - Find businesses with weak GBP
2. Pitch Generator - Create personalized outreach content  
3. Outreach Engine - Multi-channel message delivery
4. Booking Handler - Calendly webhook to CRM
5. Onboarding Flow - Automated client setup
6. GBP Optimizer - Google Business Profile automation
7. Reporting Engine - Performance analytics with AI
8. Finance Tracker - Revenue and expense tracking
9. Self-Learning - Feedback loop for improvement

You help users interact with these layers and provide guidance on business automation workflows."""

    system_message = SystemMessage(content=system_content)
    
    messages = [system_message]
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            messages.append(msg)
        elif isinstance(msg, AIMessage):
            messages.append(msg)
    
    try:
        response = await model.ainvoke(messages)
        return {"messages": [response]}
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error processing request: {str(e)}")]}

# Create the CEP Machine graph
graph = StateGraph(CEPState)
graph.add_node("cep_llm", cep_llm)
graph.add_edge(START, "cep_llm")
graph.add_edge("cep_llm", END)
graph = graph.compile()
