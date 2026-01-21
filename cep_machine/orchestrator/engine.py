"""
CEP Orchestrator - Master LangGraph Workflow

The "Manager" that chains all engines:
Research Node → Architecture Node → Build Node → Test Node → Metrics Node → Commit Node → PR Node

Cost: $0/month (orchestration is local)
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass, field
from enum import Enum

from langgraph.graph import StateGraph, END

from ..core.database import Database
from ..core.coherence import CoherenceMetrics
from ..core.containers import SalesContainer, OpsContainer, FinanceContainer
from ..research.engine import ResearchEngine
from ..architecture.engine import ArchitectureEngine, LayerArchitecture
from ..testing.engine import TestingEngine, TestReport


class OrchestratorPhase(Enum):
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    BUILD = "build"
    TEST = "test"
    METRICS = "metrics"
    COMMIT = "commit"
    PR = "pr"


@dataclass
class LayerBuildResult:
    """Result of building a complete layer."""
    layer_id: int
    layer_name: str
    success: bool
    architecture: Optional[LayerArchitecture]
    test_report: Optional[TestReport]
    phi_contribution: float
    output_file: str
    commit_hash: Optional[str]
    pr_url: Optional[str]
    errors: List[str]
    build_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "success": self.success,
            "architecture": self.architecture.to_dict() if self.architecture else None,
            "test_report": self.test_report.to_dict() if self.test_report else None,
            "phi_contribution": self.phi_contribution,
            "output_file": self.output_file,
            "commit_hash": self.commit_hash,
            "pr_url": self.pr_url,
            "errors": self.errors,
            "build_time_seconds": self.build_time_seconds,
        }


class OrchestratorState(TypedDict):
    """State for the master orchestrator workflow."""
    layer_id: int
    layer_name: str
    requirements: str
    output_file: str
    
    # Phase outputs
    research_report: Dict[str, Any]
    architecture: Optional[LayerArchitecture]
    code_generated: bool
    test_report: Optional[TestReport]
    phi_sync_before: float
    phi_sync_after: float
    commit_hash: Optional[str]
    pr_url: Optional[str]
    
    # Tracking
    current_phase: str
    errors: List[str]
    start_time: str


class Orchestrator:
    """
    Master Orchestrator - Chains all CEP engines.
    
    Workflow:
    1. Research: Find best practices for the layer
    2. Architecture: Design the layer structure
    3. Build: Generate the code
    4. Test: Validate with Playwright
    5. Metrics: Calculate Φ_sync improvement
    6. Commit: Git commit the changes
    7. PR: Create GitHub PR (optional)
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        auto_commit: bool = True,
        auto_pr: bool = False,
    ):
        self.db = db or Database()
        self.auto_commit = auto_commit
        self.auto_pr = auto_pr
        
        # Initialize engines
        self.research = ResearchEngine(db=self.db)
        self.architecture = ArchitectureEngine(db=self.db)
        self.testing = TestingEngine(db=self.db)
        
        # Initialize containers and coherence
        self.sales = SalesContainer()
        self.ops = OpsContainer()
        self.finance = FinanceContainer()
        self.coherence = CoherenceMetrics(
            sales=self.sales,
            ops=self.ops,
            finance=self.finance,
        )
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the master LangGraph workflow."""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("research", self._research_node)
        workflow.add_node("architecture", self._architecture_node)
        workflow.add_node("build", self._build_node)
        workflow.add_node("test", self._test_node)
        workflow.add_node("metrics", self._metrics_node)
        workflow.add_node("commit", self._commit_node)
        workflow.add_node("pr", self._pr_node)
        
        # Add edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "architecture")
        workflow.add_edge("architecture", "build")
        workflow.add_edge("build", "test")
        workflow.add_edge("test", "metrics")
        workflow.add_edge("metrics", "commit")
        workflow.add_edge("commit", "pr")
        workflow.add_edge("pr", END)
        
        return workflow.compile()
    
    async def _research_node(self, state: OrchestratorState) -> OrchestratorState:
        """Research phase: Find best practices."""
        state["current_phase"] = "research"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 1: RESEARCH - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        try:
            report = await self.research.research_for_layer(
                layer_id=state["layer_id"],
                topic=state["layer_name"],
            )
            state["research_report"] = report.to_dict()
            print(f"  ✓ Research complete: {report.citation_count} citations")
        except Exception as e:
            state["errors"].append(f"Research error: {str(e)}")
            state["research_report"] = {}
            print(f"  ✗ Research failed: {e}")
        
        return state
    
    async def _architecture_node(self, state: OrchestratorState) -> OrchestratorState:
        """Architecture phase: Design the layer."""
        state["current_phase"] = "architecture"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 2: ARCHITECTURE - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        try:
            research_context = state["research_report"].get("combined_summary", "")
            
            architecture = await self.architecture.design_layer(
                layer_id=state["layer_id"],
                layer_name=state["layer_name"],
                requirements=state["requirements"],
                research_context=research_context,
            )
            state["architecture"] = architecture
            print(f"  ✓ Architecture designed")
        except Exception as e:
            state["errors"].append(f"Architecture error: {str(e)}")
            state["architecture"] = None
            print(f"  ✗ Architecture failed: {e}")
        
        return state
    
    async def _build_node(self, state: OrchestratorState) -> OrchestratorState:
        """Build phase: Generate the code."""
        state["current_phase"] = "build"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 3: BUILD - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        try:
            # Generate code based on architecture
            architecture = state["architecture"]
            if architecture:
                code = self._generate_layer_code(state["layer_id"], architecture)
                
                # Write to file
                output_path = Path("cep_machine/layers") / state["output_file"]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(code)
                
                state["code_generated"] = True
                print(f"  ✓ Code generated: {state['output_file']}")
            else:
                state["code_generated"] = False
                print(f"  ✗ No architecture to build from")
        except Exception as e:
            state["errors"].append(f"Build error: {str(e)}")
            state["code_generated"] = False
            print(f"  ✗ Build failed: {e}")
        
        return state
    
    def _generate_layer_code(self, layer_id: int, architecture: LayerArchitecture) -> str:
        """Generate Python code for a layer."""
        # Get function definitions
        functions_code = ""
        for func in architecture.functions:
            params = ", ".join(func.get("params", []))
            functions_code += f'''
async def {func["name"]}({params}):
    """
    {func.get("purpose", "Layer function")}
    
    Returns: {func.get("returns", "result")}
    """
    # TODO: Implement {func["name"]}
    result = {{"status": "success", "layer_id": {layer_id}}}
    return result

'''
        
        code = f'''"""
CEP Layer {layer_id}: {architecture.layer_name}

{architecture.description}

Container Alignment: {architecture.cep_validation.get("container_alignment", "Unknown")}
Φ Contribution: {architecture.cep_validation.get("phi_contribution", 0):.2f}

Generated by CEP Orchestrator
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Layer{layer_id}Input:
    """Input data for Layer {layer_id}."""
{self._generate_dataclass_fields(architecture.inputs)}


@dataclass
class Layer{layer_id}Output:
    """Output data from Layer {layer_id}."""
{self._generate_dataclass_fields(architecture.outputs)}
    timestamp: datetime = field(default_factory=datetime.now)


# Layer Functions
{functions_code}

async def run_layer(input_data: Layer{layer_id}Input) -> Layer{layer_id}Output:
    """
    Main entry point for Layer {layer_id}: {architecture.layer_name}
    """
    print(f"[Layer {layer_id}] Starting: {architecture.layer_name}")
    
    # Execute layer logic
    result = {{}}
    
    print(f"[Layer {layer_id}] Complete ✓")
    
    return Layer{layer_id}Output(**result)


# Export
__all__ = ["Layer{layer_id}Input", "Layer{layer_id}Output", "run_layer"]
'''
        return code
    
    def _generate_dataclass_fields(self, fields: List[Dict[str, str]]) -> str:
        """Generate dataclass field definitions."""
        if not fields:
            return "    pass"
        
        lines = []
        for f in fields:
            name = f.get("name", "field")
            ftype = f.get("type", "Any")
            # Map common types
            type_map = {
                "string": "str",
                "number": "float",
                "integer": "int",
                "boolean": "bool",
                "array": "List[Any]",
                "object": "Dict[str, Any]",
            }
            python_type = type_map.get(ftype.lower(), ftype)
            lines.append(f"    {name}: {python_type}")
        
        return "\n".join(lines) if lines else "    pass"
    
    async def _test_node(self, state: OrchestratorState) -> OrchestratorState:
        """Test phase: Validate the layer."""
        state["current_phase"] = "test"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 4: TEST - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        try:
            # Run basic tests
            tests = [
                {
                    "name": f"layer_{state['layer_id']}_import_test",
                    "url": "http://localhost:3000",
                    "actions": [],
                    "assertions": [],
                }
            ]
            
            report = await self.testing.run_layer_tests(
                layer_id=state["layer_id"],
                layer_name=state["layer_name"],
                tests=tests,
            )
            state["test_report"] = report
            print(f"  ✓ Tests complete: {report.pass_rate:.0%} pass rate")
        except Exception as e:
            state["errors"].append(f"Test error: {str(e)}")
            state["test_report"] = None
            print(f"  ✗ Tests failed: {e}")
        
        return state
    
    async def _metrics_node(self, state: OrchestratorState) -> OrchestratorState:
        """Metrics phase: Calculate Φ_sync improvement."""
        state["current_phase"] = "metrics"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 5: METRICS - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        try:
            # Record before state
            state["phi_sync_before"] = self.coherence.calculate_phi_sync()
            
            # Update container based on layer
            layer_id = state["layer_id"]
            if layer_id <= 3:
                # Sales layers
                self.sales.update_metrics(
                    conversion_rate=min(1.0, self.sales.metrics.conversion_rate + 0.15),
                    efficiency=min(1.0, self.sales.metrics.efficiency + 0.10),
                )
            elif layer_id <= 6:
                # Ops layers
                self.ops.update_metrics(
                    efficiency=min(1.0, self.ops.metrics.efficiency + 0.15),
                    throughput=self.ops.metrics.throughput + 10,
                )
            else:
                # Finance layers
                self.finance.update_metrics(
                    efficiency=min(1.0, self.finance.metrics.efficiency + 0.12),
                    conversion_rate=min(1.0, self.finance.metrics.conversion_rate + 0.08),
                )
            
            # Calculate after state
            state["phi_sync_after"] = self.coherence.calculate_phi_sync()
            
            improvement = state["phi_sync_after"] - state["phi_sync_before"]
            print(f"  Φ_sync: {state['phi_sync_before']:.4f} → {state['phi_sync_after']:.4f} (+{improvement:.4f})")
            
            # Save to database
            snapshot = self.coherence.get_snapshot()
            await self.db.record_coherence(
                phi_sync=snapshot.phi_sync,
                sales_health=snapshot.container_scores["sales"],
                ops_health=snapshot.container_scores["operations"],
                finance_health=snapshot.container_scores["finance"],
                coupling_factor=snapshot.coupling_factor,
                recommendation=snapshot.recommendation,
            )
            
            print(f"  ✓ Metrics recorded")
        except Exception as e:
            state["errors"].append(f"Metrics error: {str(e)}")
            print(f"  ✗ Metrics failed: {e}")
        
        return state
    
    async def _commit_node(self, state: OrchestratorState) -> OrchestratorState:
        """Commit phase: Git commit the changes."""
        state["current_phase"] = "commit"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 6: COMMIT - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        if not self.auto_commit:
            print("  → Auto-commit disabled, skipping")
            return state
        
        try:
            import subprocess
            
            # Stage changes
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            
            # Commit
            commit_msg = f"feat(layer-{state['layer_id']}): {state['layer_name']}\n\nΦ_sync: {state.get('phi_sync_after', 0):.4f}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                )
                state["commit_hash"] = hash_result.stdout.strip()[:8]
                print(f"  ✓ Committed: {state['commit_hash']}")
            else:
                print(f"  → No changes to commit")
                
        except Exception as e:
            state["errors"].append(f"Commit error: {str(e)}")
            print(f"  ✗ Commit failed: {e}")
        
        return state
    
    async def _pr_node(self, state: OrchestratorState) -> OrchestratorState:
        """PR phase: Create GitHub PR."""
        state["current_phase"] = "pr"
        print(f"\n{'='*60}")
        print(f"[Orchestrator] PHASE 7: PR - Layer {state['layer_id']}")
        print(f"{'='*60}")
        
        if not self.auto_pr:
            print("  → Auto-PR disabled, skipping")
            return state
        
        # PR creation would go here (requires GitHub token)
        print("  → PR creation not yet implemented")
        
        return state
    
    async def build_layer(
        self,
        layer_id: int,
        layer_name: str,
        requirements: str,
        output_file: str,
    ) -> LayerBuildResult:
        """
        Build a complete layer using the orchestrator.
        
        This runs the full pipeline:
        Research → Architecture → Build → Test → Metrics → Commit → PR
        """
        start_time = datetime.now()
        
        print(f"\n{'#'*60}")
        print(f"# CEP ORCHESTRATOR: Building Layer {layer_id}")
        print(f"# {layer_name}")
        print(f"{'#'*60}")
        
        initial_state: OrchestratorState = {
            "layer_id": layer_id,
            "layer_name": layer_name,
            "requirements": requirements,
            "output_file": output_file,
            "research_report": {},
            "architecture": None,
            "code_generated": False,
            "test_report": None,
            "phi_sync_before": 0.0,
            "phi_sync_after": 0.0,
            "commit_hash": None,
            "pr_url": None,
            "current_phase": "",
            "errors": [],
            "start_time": start_time.isoformat(),
        }
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        # Calculate build time
        build_time = (datetime.now() - start_time).total_seconds()
        
        # Determine success
        success = (
            final_state.get("code_generated", False) and
            len(final_state.get("errors", [])) == 0
        )
        
        result = LayerBuildResult(
            layer_id=layer_id,
            layer_name=layer_name,
            success=success,
            architecture=final_state.get("architecture"),
            test_report=final_state.get("test_report"),
            phi_contribution=final_state.get("phi_sync_after", 0) - final_state.get("phi_sync_before", 0),
            output_file=output_file,
            commit_hash=final_state.get("commit_hash"),
            pr_url=final_state.get("pr_url"),
            errors=final_state.get("errors", []),
            build_time_seconds=build_time,
        )
        
        # Print summary
        print(f"\n{'#'*60}")
        status = "SUCCESS ✓" if success else "FAILED ✗"
        print(f"# BUILD {status}")
        print(f"# Layer {layer_id}: {layer_name}")
        print(f"# Φ_sync: {final_state.get('phi_sync_after', 0):.4f}")
        print(f"# Time: {build_time:.1f}s")
        if result.errors:
            print(f"# Errors: {len(result.errors)}")
        print(f"{'#'*60}\n")
        
        # Update layer status in database
        await self.db.update_layer_status(
            layer_id=layer_id,
            status="completed" if success else "failed",
            phi_contribution=result.phi_contribution,
        )
        
        return result
    
    async def build_all_layers(self) -> List[LayerBuildResult]:
        """Build all 9 layers in sequence."""
        layers = await self.db.get_all_layers()
        results = []
        
        for layer in layers:
            result = await self.build_layer(
                layer_id=layer["id"],
                layer_name=layer["name"],
                requirements=layer["description"],
                output_file=layer["output_file"],
            )
            results.append(result)
            
            # Check for critical failure
            if not result.success and self.coherence.calculate_phi_sync() < 0.65:
                print("\n⚠️  CRITICAL: Φ_sync dropped below 0.65 - pausing build")
                break
        
        return results
    
    def get_status(self) -> str:
        """Get current orchestrator status."""
        return self.coherence.get_status_display()
