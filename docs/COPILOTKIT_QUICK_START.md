# CopilotKit Quick Start Guide for CEP Machine

## Prerequisites
- Node.js 18+ installed
- Python 3.10+ installed
- OpenAI API key
- CopilotKit Cloud account

## Step 1: Frontend Setup

### Install CopilotKit Packages
```bash
cd apps/frontend
npm install @copilotkit/react-core @copilotkit/react-ui
```

### Configure CopilotKit Provider
```typescript
// apps/frontend/src/app/layout.tsx
import { CopilotKit } from "@copilotkit/react-core";

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <CopilotKit runtimeUrl="/api/copilotkit">
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

### Add Chat Interface
```typescript
// apps/frontend/src/app/page.tsx
import { CopilotSidebar, CopilotChat } from "@copilotkit/react-ui";

export default function HomePage() {
  return (
    <div className="flex h-screen">
      <CopilotSidebar
        title="CEP Assistant"
        instructions="I help you manage business automation workflows"
      />
      <main className="flex-1 p-4">
        <h1>CEP Machine Dashboard</h1>
        <CopilotChat />
      </main>
    </div>
  );
}
```

## Step 2: Backend Setup

### Install Python Dependencies
```bash
cd apps/agent
pip install copilotkit fastapi uvicorn openai
```

### Create CopilotKit Runtime
```python
# apps/agent/main.py
from fastapi import FastAPI
from copilotkit import CopilotRuntime, OpenAIAdapter

app = FastAPI()

# Configure CopilotKit runtime
runtime = CopilotRuntime(
    adapters=[OpenAIAdapter(api_key="your-openai-key")]
)

@app.post("/copilotkit")
async def copilot_endpoint(request):
    return await runtime.handle_request(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Step 3: Create First Agent

### Prospect Research Agent
```python
# apps/agent/agents/prospect_research.py
from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware

# Custom tools
async def search_businesses(query: str, location: str):
    """Search for businesses"""
    # Your search logic here
    return [{"name": "Example Business", "location": location}]

async def score_prospect(business_data: dict):
    """Score a prospect"""
    # Your scoring logic here
    return 85.5

# Create agent
prospect_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[
        search_businesses,
        score_prospect
    ],
    middleware=[CopilotKitMiddleware()],
    system_prompt="You are a B2B prospect research specialist. Find and score potential business prospects."
)
```

### Register Agent
```python
# apps/agent/main.py
from agents.prospect_research import prospect_agent

# Add to runtime configuration
runtime = CopilotRuntime(
    adapters=[OpenAIAdapter()],
    agents={
        "prospect_research": prospect_agent
    }
)
```

## Step 4: Connect Frontend to Agent

### Use Agent in Component
```typescript
// apps/frontend/src/components/ProspectResearch.tsx
"use client";

import { useCoAgent } from "@copilotkit/react-core";
import { useState } from "react";

export default function ProspectResearch() {
  const { state, run } = useCoAgent({
    name: "prospect_research",
    initialState: {
      prospects: [],
      status: "idle"
    }
  });

  const handleSearch = async () => {
    await run({
      action: "search",
      data: {
        query: "restaurants in New York",
        max_results: 10
      }
    });
  };

  return (
    <div className="p-4">
      <h2>Prospect Research</h2>
      <button onClick={handleSearch}>
        Search Prospects
      </button>
      
      {state.status === "searching" && (
        <p>Searching for prospects...</p>
      )}
      
      {state.prospects.length > 0 && (
        <div>
          <h3>Found {state.prospects.length} prospects</h3>
          <ul>
            {state.prospects.map((prospect, i) => (
              <li key={i}>
                {prospect.name} - Score: {prospect.score}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## Step 5: Test Integration

### Start Backend
```bash
cd apps/agent
python main.py
```

### Start Frontend
```bash
cd apps/frontend
npm run dev
```

### Test in Browser
1. Open http://localhost:3000
2. Use the chat sidebar to interact
3. Type: "Search for restaurants in New York"
4. Watch the agent process and return results

## Step 6: Add More Agents

### Pitch Generator Agent
```python
# apps/agent/agents/pitch_generator.py
from deepagents import create_deep_agent
from copilotkit import CopilotKitMiddleware

async def generate_pitch(prospect_data: dict, channel: str):
    """Generate personalized pitch"""
    # Your pitch generation logic here
    return {
        "subject": "Partnership Opportunity",
        "body": "I'd like to discuss how we can help your business grow...",
        "confidence": 0.85
    }

pitch_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[generate_pitch],
    middleware=[CopilotKitMiddleware()],
    system_prompt="You are a expert at creating personalized business pitches."
)
```

### Outreach Engine (CrewAI)
```python
# apps/agent/agents/outreach_engine.py
from crewai import Flow, Agent, Task
from copilotkit import CopilotKitMiddleware

class OutreachFlow(Flow):
    @start()
    def plan_sequence(self):
        """Plan outreach sequence"""
        return {"sequence": ["email", "followup", "call"]}
    
    @listen("plan_sequence")
    def send_email(self):
        """Send initial email"""
        # Email sending logic
        return {"status": "email_sent"}
    
    @listen("send_email")
    def schedule_followup(self):
        """Schedule follow-up"""
        # Follow-up scheduling
        return {"status": "followup_scheduled"}

outreach_agent = OutreachFlow()
```

## Step 7: Advanced Features

### Human-in-the-Loop
```python
# apps/agent/agents/booking_handler.py
from copilotkit import HumanInTheLoop

@HumanInTheLoop
def confirm_meeting(meeting_details):
    """Require human approval for meetings"""
    return {
        "type": "approval_request",
        "message": f"Confirm meeting with {meeting_details['prospect']}?",
        "data": meeting_details
    }
```

### AG-UI Dashboard
```python
# apps/agent/agents/reporting_engine.py
from copilotkit import AGUI

@AGUI
def generate_dashboard(state):
    """Generate dynamic dashboard"""
    return {
        "type": "dashboard",
        "components": [
            {
                "type": "chart",
                "chart_type": "line",
                "data": state.metrics,
                "title": "Performance Trends"
            },
            {
                "type": "table",
                "data": state.reports,
                "title": "Summary Report"
            }
        ]
    }
```

## Step 8: Production Considerations

### Environment Variables
```bash
# .env
OPENAI_API_KEY=sk-your-key
COPILOTKIT_API_KEY=ck-your-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoring
```python
# apps/agent/monitoring.py
from prometheus_client import Counter, Histogram

agent_requests = Counter('agent_requests_total', 'Total agent requests')
agent_duration = Histogram('agent_duration_seconds', 'Agent execution time')

async def track_agent_execution(agent_name, func):
    """Track agent execution metrics"""
    start_time = time.time()
    try:
        result = await func()
        agent_requests.labels(agent=agent_name).inc()
        return result
    finally:
        agent_duration.labels(agent=agent_name).observe(time.time() - start_time)
```

## Common Issues & Solutions

### Issue: Agent not responding
**Solution:** Check runtime configuration and API keys
```python
# Verify runtime is configured correctly
print(runtime.adapters)
print(runtime.agents.keys())
```

### Issue: Frontend not connecting
**Solution:** Ensure runtime URL is correct
```typescript
// Check runtime URL
<CopilotKit runtimeUrl="http://localhost:8000/api/copilotkit">
```

### Issue: Tools not working
**Solution:** Verify tool registration
```python
# Ensure tools are properly registered
print(prospect_agent.tools)
```

## Next Steps

1. **Implement remaining agents** following the patterns above
2. **Add database integration** for persistent state
3. **Implement caching** with Redis
4. **Add monitoring** with Prometheus/Grafana
5. **Deploy to production** with Docker

## Resources

- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [Deep Agents Guide](https://docs.copilotkit.ai/coagents)
- [CrewAI Documentation](https://docs.crewai.com/)
- [AG-UI Protocol](https://www.ag-ui.org/)

## Support

For issues:
1. Check the CopilotKit documentation
2. Review the agent logs
3. Test with simple examples first
4. Join the CopilotKit Discord community

This quick start guide provides the essential steps to get CopilotKit integrated with your CEP Machine. Start with the basic setup and gradually add more complex features as needed.
