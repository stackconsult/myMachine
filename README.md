# CEP Proprietary Machine

> **RULE: WE NEVER MAP IN TIMEFRAMES, WE MAP IN STEPS**

A 9-layer AI agent framework that replaces $475/month in SaaS tools with a $120/year proprietary system.

## What This Replaces

| External Tool | Cost | Replacement | Cost |
|---------------|------|-------------|------|
| Perplexity Comet | $200/mo | Research Engine | $0 |
| Claude Code | $200/mo | Architecture Engine | ~$10/mo |
| BrowserOS | $50-100/mo | Testing Engine | $0 |
| **Total** | **$475/mo** | **CEP Machine** | **$10/mo** |

**Annual Savings: $5,580/year**

## The 4 Engines

1. **Research Engine** - DuckDuckGo + Firecrawl + Ollama → Research with citations
2. **Architecture Engine** - LangGraph + Claude API → Auditable system design
3. **Testing Engine** - Playwright → Real browser testing
4. **Orchestrator** - Master workflow chaining all engines

## The 9 Business Layers

| Layer | Name | Purpose |
|-------|------|---------|
| 1 | Prospect Research | Find businesses with no GBP |
| 2 | Pitch Generator | Personalized outreach emails |
| 3 | Outreach Engine | Send via Gmail API |
| 4 | Booking Handler | Calendly webhook → CRM |
| 5 | Onboarding Flow | Google Drive + Trello setup |
| 6 | GBP Optimizer | Core service automation |
| 7 | Reporting Engine | PDF reports |
| 8 | Finance Tracker | Stripe webhooks → MRR |
| 9 | Self-Learning | Feedback loop for improvement |

## Coherence Metrics (Φ_sync)

| Milestone | Φ_sync | Status |
|-----------|--------|--------|
| Infrastructure Ready | 0.30 | Step 4 Complete |
| Factory Built | 0.65 | Step 8 Complete |
| Sales Container Live | 0.70 | Step 11 Complete |
| Ops Container Live | 0.80 | Step 14 Complete |
| Machine Complete | 0.88 | Step 17 Complete |
| Production Ready | 0.95+ | Step 20 Complete |

## Quick Start

```bash
# Clone and setup
git clone https://github.com/stackconsult/myMachine.git
cd myMachine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup local AI
ollama pull llama2
playwright install chromium

# Copy environment config
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Initialize database
python -c "import asyncio; from cep_machine.core.database import Database; asyncio.run(Database().initialize())"

# Verify installation
python -m pytest tests/ -v
```

## Project Structure

```
myMachine/
├── cep_machine/
│   ├── core/           # Containers, Coherence, Database
│   ├── research/       # Research Engine
│   ├── architecture/   # Architecture Engine  
│   ├── testing/        # Testing Engine
│   ├── orchestrator/   # Master Workflow
│   └── layers/         # 9 Business Layers
├── tests/              # Unit & integration tests
├── docs/               # Documentation
├── data/               # SQLite database
├── config.yaml         # CEP configuration
└── requirements.txt    # Python dependencies
```

## Tech Stack

- **Python 3.10+**
- **LangGraph** - Workflow orchestration
- **Ollama** - Local LLM (llama2/mistral)
- **Playwright** - Browser automation
- **SQLite** - Local database
- **DuckDuckGo** - Web search (free)
- **Firecrawl** - Web crawling
- **Claude API** - Architecture reasoning (~$10/mo)

## License

MIT

---

*Built with discipline. Mapped in steps, not timeframes.*