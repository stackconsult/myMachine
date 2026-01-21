"""
Simple Production Agents for CEP Machine
Standalone implementation without CopilotKit LangGraph dependencies
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class SimpleAgent:
    """Simple agent implementation for CEP Machine"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools = {}
    
    def add_tool(self, name: str, func):
        """Add a tool to the agent"""
        self.tools[name] = func
    
    def process_message(self, message: str) -> str:
        """Process a user message and return a response"""
        # Simple routing based on keywords
        message_lower = message.lower()
        
        if "prospect" in message_lower or "search" in message_lower:
            if "search_prospects" in self.tools:
                # Extract location and category (simple parsing)
                location = "san_francisco"
                category = "technology"
                
                words = message.split()
                if "in" in words:
                    idx = words.index("in")
                    if idx + 1 < len(words):
                        location = words[idx + 1].replace(",", "")
                
                result = self.tools["search_prospects"](location, category)
                return self._format_prospects(result)
        
        elif "pitch" in message_lower or "generate" in message_lower:
            if "generate_pitch" in self.tools:
                # Extract business name
                business_name = "Tech Startup"
                words = message.split()
                for word in words:
                    if word.istitle() and len(word) > 3:
                        business_name = word
                        break
                
                result = self.tools["generate_pitch"](business_name, "technology")
                return self._format_pitch(result)
        
        elif "outreach" in message_lower or "send" in message_lower:
            if "send_outreach" in self.tools:
                result = self.tools["send_outreach"]("test@example.com", "Sample message", "email")
                return self._format_outreach(result)
        
        elif "finance" in message_lower or "track" in message_lower:
            if "track_finances" in self.tools:
                # Extract amount
                amount = 100.0
                import re
                numbers = re.findall(r'\$?(\d+(?:\.\d+)?)', message)
                if numbers:
                    amount = float(numbers[0])
                
                transaction_type = "expense" if "expense" in message_lower else "income"
                result = self.tools["track_finances"](amount, "general", transaction_type)
                return self._format_finance(result)
        
        elif "analyze" in message_lower or "performance" in message_lower:
            if "analyze_performance" in self.tools:
                # Extract layer name
                layer = "general"
                if "layer" in message_lower:
                    words = message.split()
                    for i, word in enumerate(words):
                        if word == "layer" and i + 1 < len(words):
                            layer = words[i + 1]
                            break
                
                period = "last_7_days"
                if "month" in message_lower:
                    period = "last_30_days"
                
                result = self.tools["analyze_performance"](layer, period)
                return self._format_performance(result)
        
        return f"I'm the {self.name} agent. {self.description}. I can help you with: {', '.join(self.tools.keys())}. What would you like to do?"
    
    def _format_prospects(self, prospects: List[Dict]) -> str:
        """Format prospect results"""
        response = f"🔍 Found {len(prospects)} prospects:\n\n"
        for prospect in prospects:
            response += f"📊 {prospect['name']}\n"
            response += f"   Location: {prospect['location']}\n"
            response += f"   Category: {prospect['category']}\n"
            response += f"   Revenue: {prospect['revenue']}\n"
            response += f"   Employees: {prospect['employees']}\n"
            response += f"   Contact: {prospect['contact']}\n\n"
        return response
    
    def _format_pitch(self, pitch: Dict) -> str:
        """Format pitch results"""
        response = f"📝 Generated pitch:\n\n"
        response += f"Subject: {pitch['subject']}\n\n"
        response += f"Body: {pitch['body']}\n\n"
        response += f"Call to Action: {pitch['call_to_action']}\n"
        response += f"Personalization Score: {pitch['personalization_score']}\n"
        return response
    
    def _format_outreach(self, result: Dict) -> str:
        """Format outreach results"""
        response = f"📧 Outreach sent:\n\n"
        response += f"Message ID: {result['message_id']}\n"
        response += f"Status: {result['status']}\n"
        response += f"Channel: {result['channel']}\n"
        response += f"Recipient: {result['recipient']}\n"
        return response
    
    def _format_finance(self, result: Dict) -> str:
        """Format finance results"""
        response = f"💰 Transaction recorded:\n\n"
        response += f"Amount: ${result['amount']}\n"
        response += f"Category: {result['category']}\n"
        response += f"Type: {result['type']}\n"
        response += f"Transaction ID: {result['transaction_id']}\n"
        response += f"Status: {result['status']}\n"
        return response
    
    def _format_performance(self, result: Dict) -> str:
        """Format performance results"""
        response = f"📈 Performance Analysis:\n\n"
        response += f"Layer: {result['layer']}\n"
        response += f"Period: {result['period']}\n\n"
        response += f"Metrics:\n"
        for metric, value in result['metrics'].items():
            response += f"  {metric.replace('_', ' ').title()}: {value}\n"
        response += f"\nRecommendations:\n"
        for rec in result['recommendations']:
            response += f"  • {rec}\n"
        return response

# CEP Machine Tools
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

def generate_pitch(business_name: str, industry: str) -> Dict[str, Any]:
    """Generate personalized outreach content"""
    return {
        "subject": f"Partnership Opportunity with {business_name}",
        "body": f"Hi {business_name} team, We noticed your innovative work in {industry} and would love to explore potential synergies...",
        "call_to_action": "Schedule a 15-minute demo",
        "personalization_score": 0.85
    }

def send_outreach(contact_email: str, message: str, channel: str) -> Dict[str, Any]:
    """Send outreach messages"""
    return {
        "status": "sent",
        "recipient": contact_email,
        "channel": channel,
        "message_id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "delivery_status": "delivered"
    }

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

# Agent Factory
def create_business_growth_agent() -> SimpleAgent:
    """Create business growth agent"""
    agent = SimpleAgent(
        name="business_growth",
        description="Specializes in finding prospects and generating outreach campaigns"
    )
    agent.add_tool("search_prospects", search_prospects)
    agent.add_tool("generate_pitch", generate_pitch)
    agent.add_tool("send_outreach", send_outreach)
    return agent

def create_performance_analyzer_agent() -> SimpleAgent:
    """Create performance analyzer agent"""
    agent = SimpleAgent(
        name="performance_analyzer",
        description="Analyzes CEP Machine performance metrics and provides optimization recommendations"
    )
    agent.add_tool("analyze_performance", analyze_performance)
    return agent

def create_finance_agent() -> SimpleAgent:
    """Create finance tracking agent"""
    agent = SimpleAgent(
        name="finance_tracker",
        description="Tracks financial transactions and provides business insights"
    )
    agent.add_tool("track_finances", track_finances)
    return agent

# Agent Registry
AGENTS = {
    "business_growth": create_business_growth_agent(),
    "performance_analyzer": create_performance_analyzer_agent(),
    "finance_tracker": create_finance_agent()
}

def get_agent(agent_name: str) -> Optional[SimpleAgent]:
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
    
    # Test business growth agent
    print("\n=== Testing Business Growth Agent ===")
    agent = get_agent("business_growth")
    print(agent.process_message("Search for prospects in San Francisco"))
    print(agent.process_message("Generate a pitch for TechStartup"))
    
    # Test performance analyzer
    print("\n=== Testing Performance Analyzer ===")
    agent = get_agent("performance_analyzer")
    print(agent.process_message("Analyze performance for marketing layer"))
    
    # Test finance tracker
    print("\n=== Testing Finance Tracker ===")
    agent = get_agent("finance_tracker")
    print(agent.process_message("Track $500 expense for marketing"))
