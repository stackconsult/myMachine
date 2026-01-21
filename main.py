#!/usr/bin/env python3
"""
CEP Proprietary Machine - Main Entry Point

RULE: WE NEVER MAP IN TIMEFRAMES, WE MAP IN STEPS

Usage:
    python main.py init          # Initialize database
    python main.py status        # Show coherence status
    python main.py build <n>     # Build layer N
    python main.py build-all     # Build all 9 layers
    python main.py research <q>  # Quick research
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from cep_machine.core.database import Database
from cep_machine.core.coherence import CoherenceMetrics
from cep_machine.core.containers import SalesContainer, OpsContainer, FinanceContainer
from cep_machine.orchestrator.engine import Orchestrator


async def init_database():
    """Initialize the database."""
    print("[Init] Initializing database...")
    db = Database()
    await db.initialize()
    print("[Init] ✓ Database initialized with 9 layers")
    
    # Show layers
    layers = await db.get_all_layers()
    print("\n9 Business Layers:")
    for layer in layers:
        print(f"  Layer {layer['id']}: {layer['name']} → {layer['output_file']}")


async def show_status():
    """Show current coherence status."""
    coherence = CoherenceMetrics()
    print(coherence.get_status_display())
    
    # Show any red flags
    flags = coherence.check_red_flags()
    if flags:
        print("\n⚠️  RED FLAGS:")
        for flag in flags:
            print(f"  - {flag}")


async def build_layer(layer_id: int):
    """Build a specific layer."""
    db = Database()
    await db.initialize()
    
    layer = await db.get_layer(layer_id)
    if not layer:
        print(f"Error: Layer {layer_id} not found")
        return
    
    orchestrator = Orchestrator(db=db)
    result = await orchestrator.build_layer(
        layer_id=layer["id"],
        layer_name=layer["name"],
        requirements=layer["description"],
        output_file=layer["output_file"],
    )
    
    if result.success:
        print(f"\n✓ Layer {layer_id} built successfully!")
        print(f"  Output: {result.output_file}")
        print(f"  Φ contribution: +{result.phi_contribution:.4f}")
    else:
        print(f"\n✗ Layer {layer_id} build failed")
        for error in result.errors:
            print(f"  Error: {error}")


async def build_all_layers():
    """Build all 9 layers."""
    db = Database()
    await db.initialize()
    
    orchestrator = Orchestrator(db=db)
    results = await orchestrator.build_all_layers()
    
    # Summary
    print("\n" + "="*60)
    print("BUILD SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r.success)
    print(f"Layers built: {successful}/{len(results)}")
    
    total_phi = sum(r.phi_contribution for r in results)
    print(f"Total Φ contribution: +{total_phi:.4f}")
    
    print("\nStatus:")
    print(orchestrator.get_status())


async def quick_research(query: str):
    """Run a quick research query."""
    from cep_machine.research.engine import ResearchEngine
    
    engine = ResearchEngine()
    report = await engine.research(query)
    
    print(f"\n{'='*60}")
    print(f"Research: {query}")
    print(f"{'='*60}")
    print(f"\n{report.combined_summary}")
    print(f"\nSources ({report.citation_count}):")
    for r in report.results:
        print(f"  - {r.source_title}")
        print(f"    {r.source_url}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        asyncio.run(init_database())
    
    elif command == "status":
        asyncio.run(show_status())
    
    elif command == "build":
        if len(sys.argv) < 3:
            print("Usage: python main.py build <layer_number>")
            return
        layer_id = int(sys.argv[2])
        asyncio.run(build_layer(layer_id))
    
    elif command == "build-all":
        asyncio.run(build_all_layers())
    
    elif command == "research":
        if len(sys.argv) < 3:
            print("Usage: python main.py research <query>")
            return
        query = " ".join(sys.argv[2:])
        asyncio.run(quick_research(query))
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
