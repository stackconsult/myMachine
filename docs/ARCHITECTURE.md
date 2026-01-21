# CEP Proprietary Machine Architecture

## Overview

The CEP Proprietary Machine is a 9-layer AI agent framework designed to automate business development and operations. It follows a container-based architecture with clear separation of concerns and a coherence metric (Φ_sync) to measure system health.

## Core Components

### 1. Containers

The system is organized into three main containers:

#### Sales Container (Φ_weight: 0.33)
- **Timescale:** Daily
- **Layers:** 1-4
- **Purpose:** Lead generation to client conversion
- **Metrics:** Prospect volume, pitch rate, outreach success, booking conversion

#### Operations Container (Φ_weight: 0.33)
- **Timescale:** Weekly
- **Layers:** 5-6
- **Purpose:** Client delivery and service fulfillment
- **Metrics:** Onboarding speed, GBP optimization score, client satisfaction

#### Finance Container (Φ_weight: 0.34)
- **Timescale:** Monthly
- **Layers:** 7-9
- **Purpose:** Financial tracking and system improvement
- **Metrics:** Revenue, profit, insights generated, optimizations deployed

### 2. Coherence Metrics (Φ_sync)

Φ_sync measures the overall system coherence and health:

```
Φ_sync = Σ(container_health * container_weight)
```

Where:
- `container_health` = (conversion_rate + efficiency) / 2 - error_rate
- `container_weight` = Predefined weight (0.33, 0.33, 0.34)

### 3. The 4 Engines

#### Research Engine
- **Purpose:** Find and analyze business data
- **Tools:** DuckDuckGo + Firecrawl + Ollama
- **Output:** Structured research with citations

#### Architecture Engine
- **Purpose:** Design and validate system architectures
- **Tools:** LangGraph + Claude API
- **Output:** Auditable design documents

#### Testing Engine
- **Purpose:** Automated browser testing
- **Tools:** Playwright
- **Output:** Test results with screenshots

#### Orchestrator
- **Purpose:** Master workflow controller
- **Tools:** LangGraph
- **Output:** Coordinated execution of all engines

## Layer Architecture

### Layer 1: Prospect Research
```python
ProspectorEngine
├── search_local_businesses()
├── analyze_gbp()
└── score_prospects()
```

**Input:** Location, business category
**Output:** Qualified prospects with GBP scores
**Container:** Sales

### Layer 2: Pitch Generator
```python
PitchGeneratorEngine
├── generate_content()
├── personalize_message()
└── calculate_confidence()
```

**Input:** Prospect data
**Output:** Personalized multi-channel pitches
**Container:** Sales

### Layer 3: Outreach Engine
```python
OutreachEngine
├── create_sequences()
├── schedule_messages()
└── track_responses()
```

**Input:** Pitches, contact info
**Output:** Sent messages, response tracking
**Container:** Sales

### Layer 4: Booking Handler
```python
BookingHandler
├── process_webhooks()
├── create_meetings()
└── update_crm()
```

**Input:** Calendly webhooks
**Output:** Calendar events, CRM updates
**Container:** Sales

### Layer 5: Onboarding Flow
```python
OnboardingEngine
├── create_checklists()
├── collect_documents()
└── setup_accounts()
```

**Input:** New client data
**Output:** Onboarded client with accounts
**Container:** Operations

### Layer 6: GBP Optimizer
```python
GBPOptimizerEngine
├── analyze_profile()
├── generate_content()
└── track_improvements()
```

**Input:** Client GBP data
**Output:** Optimized GBP with improved visibility
**Container:** Operations

### Layer 7: Reporting Engine
```python
ReportingEngine
├── collect_metrics()
├── generate_insights()
└── create_reports()
```

**Input:** Data from all layers
**Output:** Performance reports with AI insights
**Container:** Finance

### Layer 8: Finance Tracker
```python
FinanceTrackerEngine
├── track_revenue()
├── calculate_metrics()
└── generate_invoices()
```

**Input:** Financial events
**Output:** Complete financial picture
**Container:** Finance

### Layer 9: Self-Learning
```python
FeedbackLoopEngine
├── analyze_performance()
├── identify_patterns()
└── generate_optimizations()
```

**Input:** System performance data
**Output:** Improvement recommendations
**Container:** Meta (All)

## Data Flow

```
Layer 1 (Prospects) → Layer 2 (Pitches) → Layer 3 (Outreach)
                                      ↓
Layer 4 (Bookings) → Layer 5 (Onboarding) → Layer 6 (GBP Opt.)
                                      ↓
Layer 7 (Reports) → Layer 8 (Finance) → Layer 9 (Learning)
                      ↑                      ↓
                      └─────── Feedback Loop ────────┘
```

## Database Schema

### Tables

1. **layers** - Layer configuration and metadata
2. **research_logs** - Research engine outputs
3. **coherence_metrics** - Φ_sync history
4. **events** - Container events
5. **architectures** - Design documents
6. **test_results** - Test outcomes

### Key Relationships

- Events → Containers (many-to-one)
- Research → Layers (one-to-many)
- Test Results → Architectures (one-to-many)

## Configuration

### config.yaml Structure

```yaml
cep:
  version: "1.0.0"
  phi_thresholds:
    infrastructure: 0.30
    factory: 0.65
    sales: 0.70
    operations: 0.80
    machine: 0.88
    production: 0.95

containers:
  sales:
    weight: 0.33
    timescale: daily
  operations:
    weight: 0.33
    timescale: weekly
  finance:
    weight: 0.34
    timescale: monthly

engines:
  research:
    max_results: 20
    citation_required: true
  architecture:
    model: "claude-3-sonnet"
    validation_rules: strict
  testing:
    browser: chromium
    headless: true
  orchestrator:
    timeout: 3600
    retry_count: 3
```

## Security Considerations

1. **API Keys:** Stored in environment variables
2. **Data Privacy:** Local SQLite database
3. **Webhook Security:** Signature validation
4. **Access Control:** Role-based permissions

## Performance Optimization

1. **Async Operations:** All I/O is async
2. **Connection Pooling:** Database connections reused
3. **Caching:** Research results cached
4. **Batch Processing:** Bulk operations where possible

## Monitoring

### Metrics Tracked

- Φ_sync coherence score
- Layer execution times
- Error rates per container
- Throughput metrics
- Resource utilization

### Health Checks

- Database connectivity
- External API status
- Container health scores
- System coherence

## Deployment

### Local Development
```bash
python -m cep_machine.main --mode=dev
```

### Production
```bash
python -m cep_machine.main --mode=prod
```

### Docker
```bash
docker build -t cep-machine .
docker run -p 8000:8000 cep-machine
```

## Extensibility

### Adding New Layers

1. Create layer file in `cep_machine/layers/`
2. Implement `run_layer()` function
3. Add to container in `containers.py`
4. Update configuration
5. Add tests

### Custom Engines

1. Create engine directory
2. Implement base interface
3. Register in orchestrator
4. Add configuration options

## Troubleshooting

### Common Issues

1. **Low Φ_sync:** Check container health
2. **Slow Performance:** Review async operations
3. **API Errors:** Verify keys and rate limits
4. **Database Issues:** Check SQLite permissions

### Debug Mode

```bash
python -m cep_machine.main --debug --layer=1
```

---

*Architecture designed for clarity, maintainability, and scalability.*
