# CopilotKit Technical Specification for CEP Machine

## Architecture Overview

### System Components
1. **Frontend Layer**
   - React/Next.js application
   - CopilotKit UI components
   - State management hooks
   - AG-UI protocol handlers

2. **Backend Layer**
   - FastAPI runtime
   - Agent orchestration
   - Tool execution environment
   - External API integrations

3. **Agent Layer**
   - Deep Agents (LangGraph)
   - CrewAI Flows
   - Custom implementations
   - State management

4. **Data Layer**
   - PostgreSQL (primary)
   - DragonflyDB (cache)
   - Vector stores (embeddings)
   - File storage

## Agent Specifications

### 1. Prospect Research Agent

**Type:** Custom Deep Agent

**Core Tools:**
```python
tools = [
    BusinessSearchTool(),      # DuckDuckGo integration
    GBPAnalysisTool(),        # Google Business Profile
    LeadScoringTool(),        # Custom scoring algorithm
    ContactExtractionTool(),  # Data enrichment
    MarketResearchTool()      # Industry analysis
]
```

**State Schema:**
```python
@dataclass
class ProspectResearchState:
    search_query: str
    location: str
    category: str
    prospects: List[Prospect]
    gbp_data: Dict[str, Any]
    scores: List[float]
    research_status: str
    completion_percentage: float
```

**Agent Flow:**
1. Parse search parameters
2. Execute business search
3. Analyze GBP presence
4. Score prospects
5. Extract contact info
6. Return ranked results

### 2. Pitch Generator Agent

**Type:** Deep Agent with LLM focus

**Core Tools:**
```python
tools = [
    PainPointAnalyzer(),       # LLM-powered analysis
    ValuePropositionGen(),     # Content generation
    PersonalizationEngine(),   # Custom logic
    ConfidenceCalculator(),    # Scoring algorithm
    TemplateManager(),         # Template system
    ChannelAdapter()          # Multi-channel output
]
```

**State Schema:**
```python
@dataclass
class PitchGenerationState:
    prospect: Prospect
    pain_points: List[str]
    value_proposition: str
    pitch_content: Dict[str, str]  # Channel -> Content
    confidence_score: float
    personalization_data: Dict[str, Any]
    generation_status: str
```

**Agent Flow:**
1. Analyze prospect data
2. Identify pain points
3. Create value proposition
4. Generate channel-specific content
5. Calculate confidence score
6. Apply personalization

### 3. Outreach Engine Agent

**Type:** CrewAI Flow

**Sub-Agents:**
```python
class EmailAgent(BaseAgent):
    """Handles email outreach"""
    tools = [EmailSender(), TemplateEngine(), Tracker()]

class SMSAgent(BaseAgent):
    """Handles SMS outreach"""
    tools = [SMSGateway(), MessageOptimizer(), ComplianceChecker()]

class LinkedInAgent(BaseAgent):
    """Handles LinkedIn outreach"""
    tools = [LinkedInAPI(), ContentOptimizer(), ConnectionManager()]

class FollowUpAgent(BaseAgent):
    """Manages follow-up sequences"""
    tools = [SequenceManager(), TimingOptimizer(), ResponseAnalyzer()]
```

**Flow Structure:**
```python
class OutreachFlow(Flow):
    @start()
    def sequence_planning(self):
        """Plan outreach sequence"""
        pass
    
    @listen("sequence_planning")
    def parallel_outreach(self):
        """Execute multi-channel outreach"""
        pass
    
    @listen("parallel_outreach")
    def response_tracking(self):
        """Track and analyze responses"""
        pass
    
    @listen("response_tracking")
    def followup_coordination(self):
        """Coordinate follow-ups"""
        pass
```

### 4. Booking Handler Agent

**Type:** Custom Agent with HITL

**Core Tools:**
```python
tools = [
    CalendarIntegration(),    # Google/Outlook APIs
    AvailabilityChecker(),    # Time zone handling
    MeetingCreator(),         # Calendar event creation
    ConfirmationManager(),   # Human approval flow
    ReschedulingHandler(),   # Change management
    NotificationSender()      # Alert system
]
```

**HITL Implementation:**
```python
@HumanInTheLoop
def confirm_meeting(meeting_details):
    """Require human approval for meetings"""
    return {
        "type": "approval_request",
        "data": meeting_details,
        "options": ["approve", "modify", "reject"]
    }
```

### 5. Onboarding Flow Agent

**Type:** CrewAI Flow

**Flow Stages:**
```python
class OnboardingFlow(Flow):
    @start()
    def data_collection(self):
        """Collect client information"""
        pass
    
    @listen("data_collection")
    def service_configuration(self):
        """Set up client services"""
        pass
    
    @listen("service_configuration")
    def document_generation(self):
        """Generate onboarding documents"""
        pass
    
    @listen("document_generation")
    def welcome_sequence(self):
        """Execute welcome workflow"""
        pass
    
    @listen("welcome_sequence")
    def progress_tracking(self):
        """Monitor onboarding progress"""
        pass
```

### 6. GBP Optimizer Agent

**Type:** Deep Agent with specialized tools

**Core Tools:**
```python
tools = [
    GBPProfileAnalyzer(),     # Google Business Profile API
    ContentGenerator(),       # AI content creation
    ReviewManager(),          # Review monitoring
    Q&AHandler(),             # Question management
    PhotoOptimizer(),         # Image enhancement
    InsightsAnalyzer(),       # Performance metrics
    SchedulingTool()          # Post scheduling
]
```

**Optimization Tasks:**
1. Profile completion analysis
2. Content generation
3. Review response automation
4. Q&A management
5. Photo optimization
6. Insights tracking

### 7. Reporting Engine Agent

**Type:** Deep Agent with AG-UI

**AG-UI Components:**
```python
@AGUI
def generate_dashboard(state):
    """Generate dynamic dashboard"""
    return {
        "type": "dashboard",
        "components": [
            {
                "type": "chart",
                "chart_type": "line",
                "data": state.metrics.over_time,
                "title": "Performance Trends"
            },
            {
                "type": "table",
                "data": state.reports.summary,
                "title": "Summary Report"
            },
            {
                "type": "kpi",
                "metrics": state.kpis.current,
                "title": "Key Metrics"
            }
        ]
    }
```

### 8. Finance Tracker Agent

**Type:** CrewAI Flow

**Flow Components:**
```python
class FinanceFlow(Flow):
    @start()
    def transaction_recording(self):
        """Record financial transactions"""
        pass
    
    @listen("transaction_recording")
    def invoice_generation(self):
        """Create and send invoices"""
        pass
    
    @listen("invoice_generation")
    def payment_processing(self):
        """Process incoming payments"""
        pass
    
    @listen("payment_processing")
    def revenue_calculation(self):
        """Calculate revenue metrics"""
        pass
    
    @listen("revenue_calculation")
    def forecasting(self):
        """Generate financial forecasts"""
        pass
```

### 9. Self-Learning Agent

**Type:** Deep Agent with ML capabilities

**Learning Components:**
```python
class LearningAgent:
    def __init__(self):
        self.pattern_recognizer = PatternRecognizer()
        self.optimizer = StrategyOptimizer()
        self.trainer = ModelTrainer()
    
    def analyze_performance(self, state):
        """Analyze system performance"""
        patterns = self.pattern_recognizer.identify(state.data)
        optimizations = self.optimizer.generate(patterns)
        
        # Emit learning state
        copilotkit_emit_state({
            "patterns": patterns,
            "optimizations": optimizations,
            "confidence": self.calculate_confidence(patterns)
        })
        
        return optimizations
```

## Integration Architecture

### Frontend Integration

**Provider Setup:**
```typescript
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar, CopilotChat } from "@copilotkit/react-ui";

export default function Layout({ children }) {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <div className="flex h-screen">
        <CopilotSidebar
          title="CEP Assistant"
          instructions="I help you manage your business automation workflows"
        />
        <main className="flex-1">
          {children}
          <CopilotChat />
        </main>
      </div>
    </CopilotKit>
  );
}
```

**State Management:**
```typescript
import { useCoAgent } from "@copilotkit/react-core";

function ProspectResearchComponent() {
  const { state, setState, run } = useCoAgent({
    name: "prospect_research",
    initialState: {
      search_query: "",
      prospects: [],
      status: "idle"
    }
  });

  const handleSearch = async (query: string) => {
    await run({
      action: "search_prospects",
      data: { query, location: "US", category: "restaurants" }
    });
  };

  return (
    <div>
      <SearchInput onSearch={handleSearch} />
      <ProspectList prospects={state.prospects} />
      <ProgressBar status={state.status} />
    </div>
  );
}
```

### Backend Integration

**FastAPI Setup:**
```python
from fastapi import FastAPI
from copilotkit import CopilotRuntime, OpenAIAdapter
from agents import *

app = FastAPI()

# Configure CopilotKit runtime
runtime = CopilotRuntime(
    adapters=[OpenAIAdapter()],
    agents={
        "prospect_research": prospect_research_agent,
        "pitch_generator": pitch_generator_agent,
        "outreach_engine": outreach_engine_agent,
        "booking_handler": booking_handler_agent,
        "onboarding_flow": onboarding_flow_agent,
        "gbp_optimizer": gbp_optimizer_agent,
        "reporting_engine": reporting_engine_agent,
        "finance_tracker": finance_tracker_agent,
        "self_learning": self_learning_agent
    }
)

@app.post("/copilotkit")
async def copilot_endpoint(request):
    """Main CopilotKit endpoint"""
    return await runtime.handle_request(request)

@app.get("/api/health")
async def health_check():
    """System health check"""
    return {"status": "healthy", "timestamp": datetime.now()}
```

**Agent Registration:**
```python
# agents/__init__.py
from .prospect_research import create_prospect_research_agent
from .pitch_generator import create_pitch_generator_agent
from .outreach_engine import create_outreach_engine_agent
from .booking_handler import create_booking_handler_agent
from .onboarding_flow import create_onboarding_flow_agent
from .gbp_optimizer import create_gbp_optimizer_agent
from .reporting_engine import create_reporting_engine_agent
from .finance_tracker import create_finance_tracker_agent
from .self_learning import create_self_learning_agent

# Initialize all agents
prospect_research_agent = create_prospect_research_agent()
pitch_generator_agent = create_pitch_generator_agent()
outreach_engine_agent = create_outreach_engine_agent()
booking_handler_agent = create_booking_handler_agent()
onboarding_flow_agent = create_onboarding_flow_agent()
gbp_optimizer_agent = create_gbp_optimizer_agent()
reporting_engine_agent = create_reporting_engine_agent()
finance_tracker_agent = create_finance_tracker_agent()
self_learning_agent = create_self_learning_agent()
```

## Data Models

### Core Data Structures

**Prospect Model:**
```python
@dataclass
class Prospect:
    id: str
    name: str
    business_type: str
    location: str
    contact_info: ContactInfo
    gbp_analysis: GBPAnalysis
    score: float
    research_date: datetime
    metadata: Dict[str, Any]
```

**Pitch Model:**
```python
@dataclass
class Pitch:
    id: str
    prospect_id: str
    content: PitchContent
    confidence_score: float
    channel: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime]
```

**Outreach Model:**
```python
@dataclass
class OutreachSequence:
    id: str
    prospect_id: str
    messages: List[OutreachMessage]
    schedule: Schedule
    status: str
    metrics: OutreachMetrics
```

**Booking Model:**
```python
@dataclass
class Booking:
    id: str
    prospect_id: str
    meeting_time: datetime
    participants: List[str]
    status: str
    calendar_event_id: str
    created_at: datetime
```

## API Specifications

### Agent Endpoints

**Prospect Research:**
```python
@app.post("/api/agents/prospect-research/search")
async def search_prospects(request: ProspectSearchRequest):
    """Search for prospects"""
    result = await prospect_research_agent.search(
        location=request.location,
        category=request.category,
        max_results=request.max_results
    )
    return result
```

**Pitch Generation:**
```python
@app.post("/api/agents/pitch-generator/generate")
async def generate_pitch(request: PitchGenerationRequest):
    """Generate pitch for prospect"""
    result = await pitch_generator_agent.generate(
        prospect_id=request.prospect_id,
        channels=request.channels,
        tone=request.tone
    )
    return result
```

**Outreach Execution:**
```python
@app.post("/api/agents/outreach-engine/execute")
async def execute_outreach(request: OutreachRequest):
    """Execute outreach sequence"""
    result = await outreach_engine_agent.execute(
        sequence_id=request.sequence_id,
        prospects=request.prospects
    )
    return result
```

### State Management Endpoints

**Get Agent State:**
```python
@app.get("/api/agents/{agent_id}/state")
async def get_agent_state(agent_id: str):
    """Get current agent state"""
    return await state_manager.get_state(agent_id)
```

**Update Agent State:**
```python
@app.put("/api/agents/{agent_id}/state")
async def update_agent_state(agent_id: str, state: Dict[str, Any]):
    """Update agent state"""
    return await state_manager.update_state(agent_id, state)
```

## Security Implementation

### Authentication
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY)
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Tool Security
```python
class SecureTool(BaseTool):
    """Base class for secure tools"""
    
    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions
    
    async def verify_permissions(self, user_id: str):
        """Verify user has required permissions"""
        user_permissions = await get_user_permissions(user_id)
        return all(perm in user_permissions for perm in self.required_permissions)
    
    async def execute(self, user_id: str, **kwargs):
        """Execute tool with permission check"""
        if await self.verify_permissions(user_id):
            return await self._execute(**kwargs)
        else:
            raise PermissionError("Insufficient permissions")
```

## Performance Optimization

### Caching Strategy
```python
from copilotkit.cache import CacheManager

cache = CacheManager()

@cache.memoize(ttl=3600)
async def search_businesses(query: str, location: str):
    """Cached business search"""
    return await duckduckgo_search(query, location)

@cache.memoize(ttl=1800)
async def generate_pitch(prospect_id: str, channel: str):
    """Cached pitch generation"""
    return await llm_generate_pitch(prospect_id, channel)
```

### Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

async def process_multiple_prospects(prospects: List[Prospect]):
    """Process multiple prospects concurrently"""
    tasks = [
        asyncio.get_event_loop().run_in_executor(
            executor, process_single_prospect, prospect
        )
        for prospect in prospects
    ]
    return await asyncio.gather(*tasks)
```

## Monitoring & Observability

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
agent_requests = Counter('agent_requests_total', 'Total agent requests', ['agent_name'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution time', ['agent_name'])
active_agents = Gauge('active_agents', 'Number of active agents')

class MetricsMiddleware:
    """Middleware for collecting metrics"""
    
    async def track_agent_execution(self, agent_name: str, func):
        """Track agent execution metrics"""
        active_agents.inc()
        start_time = time.time()
        
        try:
            result = await func()
            agent_requests.labels(agent_name=agent_name).inc()
            return result
        finally:
            agent_duration.labels(agent_name=agent_name).observe(time.time() - start_time)
            active_agents.dec()
```

### Health Checks
```python
@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check"""
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "external_apis": await check_external_apis(),
        "agents": await check_agents()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now()
    }
```

## Error Handling

### Structured Error Handling
```python
from copilotkit.errors import CopilotError, ToolError

class CEPError(CopilotError):
    """Base CEP Machine error"""
    pass

class ProspectSearchError(CEPError):
    """Prospect search failed"""
    pass

class PitchGenerationError(CEPError):
    """Pitch generation failed"""
    pass

@app.exception_handler(CEPError)
async def cep_error_handler(request, exc):
    """Handle CEP Machine errors"""
    return {
        "error": {
            "type": exc.__class__.__name__,
            "message": str(exc),
            "details": exc.details if hasattr(exc, 'details') else None
        },
        "timestamp": datetime.now()
    }
```

## Testing Framework

### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch

class TestProspectResearchAgent:
    """Test suite for Prospect Research Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        return create_prospect_research_agent()
    
    async def test_business_search(self, agent):
        """Test business search functionality"""
        with patch('agents.prospect_research.duckduckgo_search') as mock_search:
            mock_search.return_value = [{"name": "Test Business"}]
            
            result = await agent.search_businesses("restaurants", "New York")
            
            assert len(result) == 1
            assert result[0]["name"] == "Test Business"
```

### Integration Tests
```python
class TestAgentIntegration:
    """Test suite for agent integration"""
    
    async def test_prospect_to_pitch_flow(self):
        """Test complete prospect to pitch flow"""
        # Create prospect
        prospect = await prospect_agent.search_businesses(...)
        
        # Generate pitch
        pitch = await pitch_agent.generate_pitch(prospect.id)
        
        # Validate results
        assert pitch.prospect_id == prospect.id
        assert pitch.confidence_score > 0.5
```

## Deployment Configuration

### Docker Configuration
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/cep_machine
CACHE_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# External APIs
GOOGLE_BUSINESS_PROFILE_API_KEY=...
DUCKDUCKGO_API_KEY=...

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

This technical specification provides the detailed implementation guide for integrating CopilotKit with the CEP Machine, covering all aspects from agent design to deployment.
