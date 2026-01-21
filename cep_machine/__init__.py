"""
CEP Proprietary Machine
=======================

A 9-layer AI agent framework that replaces $475/month in SaaS tools
with a $120/year proprietary system.

Components:
- Research Engine (replaces Perplexity)
- Architecture Engine (replaces Claude Code)
- Testing Engine (replaces BrowserOS)
- Orchestrator (chains all components)

RULE: WE NEVER MAP IN TIMEFRAMES, WE MAP IN STEPS
"""

__version__ = "1.0.0"
__author__ = "CEP Machine"

from .core.containers import CEPContainer, SalesContainer, OpsContainer, FinanceContainer
from .core.coherence import CoherenceMetrics
from .core.database import Database

__all__ = [
    "CEPContainer",
    "SalesContainer",
    "OpsContainer", 
    "FinanceContainer",
    "CoherenceMetrics",
    "Database",
]
