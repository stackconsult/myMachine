# CEP Proprietary Machine API Documentation

## Overview

The CEP Machine provides a Python API for interacting with all 9 layers. Each layer has a `run_layer()` function that serves as the main entry point.

## Base Requirements

```python
import asyncio
from cep_machine.layers import *
```

## Layer APIs

### Layer 1: Prospect Research

```python
from cep_machine.layers.prospector import run_layer

async def find_prospects():
    result = await run_layer(
        location="Miami, FL",
        category="dental",
        max_prospects=20
    )
    return result
```

**Parameters:**
- `location` (str): City and state/province
- `category` (str): Business category
- `max_prospects` (int): Maximum prospects to return

**Returns:** `ProspectSearchResult`
- `prospects`: List of qualified prospects
- `total_found`: Total businesses found
- `hot_leads`: Count of high-priority prospects
- `warm_leads`: Count of medium-priority prospects

### Layer 2: Pitch Generator

```python
from cep_machine.layers.pitch_gen import run_layer

async def generate_pitches():
    result = await run_layer(
        prospects=[prospect_list],
        channels=[PitchChannel.EMAIL, PitchChannel.LINKEDIN]
    )
    return result
```

**Parameters:**
- `prospects` (List[Prospect]): From Layer 1
- `channels` (List[PitchChannel]): Output channels

**Returns:** `PitchGenerationResult`
- `pitches`: Generated pitch objects
- `pitches_generated`: Count created
- `avg_confidence`: Average confidence score

### Layer 3: Outreach Engine

```python
from cep_machine.layers.outreach import run_layer

async def send_outreach():
    result = await run_layer(
        pitches=[pitch_list],
        channels=[OutreachChannel.EMAIL],
        dry_run=True
    )
    return result
```

**Parameters:**
- `pitches` (List[Pitch]): From Layer 2
- `channels` (List[OutreachChannel]): Send channels
- `dry_run` (bool): Simulate if True

**Returns:** `OutreachResult`
- `sequences`: Message sequences created
- `prospects_contacted`: Number contacted
- `messages_sent`: Total messages sent

### Layer 4: Booking Handler

```python
from cep_machine.layers.booking_handler import run_layer

async def handle_booking():
    webhook = {
        "event": {"action": "invitee.created"},
        "payload": {
            "email": "client@example.com",
            "name": "John Doe",
            "event_type": "Discovery Call"
        }
    }
    result = await run_layer(
        webhook_payload=webhook,
        dry_run=True
    )
    return result
```

**Parameters:**
- `webhook_payload` (Dict): Calendly webhook data
- `signature` (str, optional): Webhook signature
- `dry_run` (bool): Simulate if True

**Returns:** `BookingResult`
- `webhook_processed`: Success status
- `meeting_created`: Meeting created flag
- `calendar_invite_sent`: Invite sent flag

### Layer 5: Onboarding Flow

```python
from cep_machine.layers.onboarding import run_layer

async def onboard_client():
    result = await run_layer(
        client_name="John Doe",
        business_name="Dental Clinic",
        email="john@clinic.com",
        phone="(555) 123-4567",
        business_type="dental",
        dry_run=True
    )
    return result
```

**Parameters:**
- `client_name` (str): Client full name
- `business_name` (str): Business name
- `email` (str): Contact email
- `phone` (str): Contact phone
- `business_type` (str): Business category
- `dry_run` (bool): Simulate if True

**Returns:** `OnboardingResult`
- `client_id`: Unique client identifier
- `status`: Onboarding status
- `tasks_completed`: Completed task count

### Layer 6: GBP Optimizer

```python
from cep_machine.layers.gbp_optimizer import run_layer

async def optimize_gbp():
    result = await run_layer(
        client_id="client_123",
        business_name="Dental Clinic",
        business_type="dental",
        current_gbp_score=45.0,
        dry_run=True
    )
    return result
```

**Parameters:**
- `client_id` (str): Client identifier
- `business_name` (str): Business name
- `business_type` (str): Business category
- `current_gbp_score` (float): Current GBP score (0-100)
- `dry_run` (bool): Simulate if True

**Returns:** `GBPOptimizationResult`
- `optimizations_completed`: Number completed
- `score_improvement`: Points improved
- `posts_created`: New posts created

### Layer 7: Reporting Engine

```python
from cep_machine.layers.reporter import run_layer

async def generate_reports():
    clients_data = [
        {
            "id": "client_1",
            "business_name": "Dental Clinic",
            "prospects_count": 10,
            "gbp_score": 75.0,
            "monthly_revenue": 1500
        }
    ]
    result = await run_layer(
        clients=clients_data,
        report_type="weekly",
        dry_run=True
    )
    return result
```

**Parameters:**
- `clients` (List[Dict]): Client performance data
- `report_type` (str): "weekly", "monthly", or "quarterly"
- `dry_run` (bool): Simulate if True

**Returns:** `ReportingResult`
- `reports_generated`: Number created
- `metrics_analyzed`: Metrics processed
- `insights_count`: AI insights generated

### Layer 8: Finance Tracker

```python
from cep_machine.layers.finance_tracker import run_layer

async def track_finances():
    clients = [
        {
            "id": "client_1",
            "business_name": "Dental Clinic",
            "billing_tier": "professional",
            "new_client": True
        }
    ]
    result = await run_layer(
        clients=clients,
        dry_run=True
    )
    return result
```

**Parameters:**
- `clients` (List[Dict]): Client billing data
- `dry_run` (bool): Simulate if True

**Returns:** `FinanceTrackerResult`
- `transactions_processed`: Number processed
- `invoices_generated`: Invoices created
- `payments_received`: Payment total

### Layer 9: Self-Learning

```python
from cep_machine.layers.feedback_loop import run_layer

async def analyze_performance():
    performance_data = {
        "prospector": {"conversion_rate": 15.0},
        "pitch_gen": {"confidence_score": 0.80},
        "outreach": {"response_rate": 0.35}
    }
    historical = [
        {"phi_sync": 0.80, "date": "2026-01-01"},
        {"phi_sync": 0.85, "date": "2026-01-08"}
    ]
    result = await run_layer(
        performance_data=performance_data,
        phi_sync=0.88,
        historical_data=historical,
        dry_run=True
    )
    return result
```

**Parameters:**
- `performance_data` (Dict): Layer metrics
- `phi_sync` (float): Current coherence score
- `historical_data` (List[Dict]): Historical performance
- `dry_run` (bool): Simulate if True

**Returns:** `FeedbackLoopResult`
- `insights_generated`: Insights created
- `optimizations_created`: Optimizations identified
- `phi_sync_improvement`: Expected improvement

## Container APIs

### Sales Container

```python
from cep_machine.core.containers import SalesContainer

sales = SalesContainer()

# Record events
sales.record_prospect({"business": "Dental Clinic"})
sales.record_pitch({"confidence": 0.85})
sales.record_outreach({"channel": "email"})
sales.record_booking({"meeting_id": "123"})

# Get metrics
metrics = sales.get_metrics()
print(f"Conversion rate: {metrics['conversion_rate']}")
```

### Operations Container

```python
from cep_machine.core.containers import OpsContainer

ops = OpsContainer()

# Record events
ops.record_onboarding({"client_id": "123"})
ops.record_gbp_optimization({"score_improvement": 25})

# Get metrics
metrics = ops.get_metrics()
print(f"Efficiency: {metrics['efficiency']}")
```

### Finance Container

```python
from cep_machine.core.containers import FinanceContainer

finance = FinanceContainer()

# Record events
finance.record_report({"type": "weekly"})
finance.record_revenue({"amount": 1500})
finance.record_expense({"category": "software", "amount": 100})

# Get metrics
metrics = finance.get_metrics()
print(f"Profit margin: {metrics['profit_margin']}")
```

## Coherence Metrics

```python
from cep_machine.core.coherence import CoherenceMetrics

coherence = CoherenceMetrics()

# Calculate system coherence
phi_sync = coherence.calculate_phi_sync([
    sales_container,
    ops_container,
    finance_container
])

# Get status
status = coherence.get_status(phi_sync)
print(f"System status: {status}")
```

## Database Operations

```python
from cep_machine.core.database import Database

db = Database()

# Initialize
await db.initialize()

# Store research
await db.store_research_result(
    layer="prospector",
    query="dental miami",
    result={"prospects": [...]}
)

# Store metrics
await db.store_coherence_metrics(
    phi_sync=0.88,
    container_metrics={"sales": 0.90, "ops": 0.85, "finance": 0.87}
)

# Query data
research = await db.get_research_history(limit=10)
metrics = await db.get_coherence_history(days=30)
```

## Error Handling

```python
try:
    result = await run_layer(...)
except ValidationError as e:
    print(f"Invalid input: {e}")
except APIError as e:
    print(f"External API error: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
```

## Configuration

```python
from cep_machine.core.config import Config

config = Config()

# Get layer configuration
layer_config = config.get_layer_config("prospector")
print(f"Max results: {layer_config['max_results']}")

# Get thresholds
thresholds = config.get_phi_thresholds()
print(f"Machine complete threshold: {thresholds['machine']}")
```

## Testing

```python
# Run single layer test
python -m pytest tests/test_layer1.py -v

# Run integration test
python -m pytest tests/test_integration.py -v

# Run all tests
python -m pytest tests/ -v
```

## Best Practices

1. **Always use dry_run=True** for testing
2. **Handle exceptions** for external API calls
3. **Log events** for debugging
4. **Monitor Φ_sync** for system health
5. **Batch operations** when possible

## Rate Limits

| Service | Limit | Period |
|---------|-------|--------|
| DuckDuckGo | 100 | 1 hour |
| Firecrawl | 250 | 1 month |
| Claude API | 1000 | 1 day |
| Playwright | Unlimited | - |

---

*API designed for simplicity and flexibility.*
