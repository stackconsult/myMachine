"""
CEP Coherence Metrics - The Math Engine for Φ_sync

Container-Event Physics defines system coherence as:
Φ_sync = Σ(container_weight × container_health) × coupling_factor

Coherence Thresholds:
- 0.30: Baseline (infrastructure ready)
- 0.65: Factory built (engines complete)
- 0.70: Sales container live
- 0.80: Ops container live
- 0.88: Machine complete
- 0.95+: Production ready (scale aggressively)

Red Flags:
- < 0.85: PAUSE and fix system
- 0.85-0.90: Slow down, hire support
- 0.90-0.95: Scale steadily
- ≥ 0.95: Scale aggressively
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import math

from .containers import CEPContainer, SalesContainer, OpsContainer, FinanceContainer


@dataclass
class CoherenceSnapshot:
    """A point-in-time snapshot of system coherence."""
    phi_sync: float
    timestamp: datetime
    container_scores: Dict[str, float]
    coupling_factor: float
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phi_sync": self.phi_sync,
            "timestamp": self.timestamp.isoformat(),
            "container_scores": self.container_scores,
            "coupling_factor": self.coupling_factor,
            "recommendation": self.recommendation,
        }


class CoherenceMetrics:
    """
    The math engine for calculating Φ_sync (system coherence).
    
    Φ_sync measures how well the three containers (Sales, Ops, Finance)
    are synchronized and working together.
    """
    
    # Coherence thresholds
    BASELINE = 0.30
    FACTORY_BUILT = 0.65
    SALES_LIVE = 0.70
    OPS_LIVE = 0.80
    MACHINE_COMPLETE = 0.88
    PRODUCTION_READY = 0.95
    
    def __init__(
        self,
        sales: Optional[SalesContainer] = None,
        ops: Optional[OpsContainer] = None,
        finance: Optional[FinanceContainer] = None,
    ):
        self.sales = sales or SalesContainer()
        self.ops = ops or OpsContainer()
        self.finance = finance or FinanceContainer()
        self.history: List[CoherenceSnapshot] = []
    
    def calculate_phi_sync(self) -> float:
        """
        Calculate the system coherence score (Φ_sync).
        
        Formula:
        Φ_sync = Σ(container_weight × container_health) × coupling_factor
        
        Where coupling_factor measures how well containers work together.
        """
        # Get individual container health scores
        sales_health = self.sales.calculate_health()
        ops_health = self.ops.calculate_health()
        finance_health = self.finance.calculate_health()
        
        # Weighted sum of container health
        weighted_health = (
            self.sales.weight * sales_health +
            self.ops.weight * ops_health +
            self.finance.weight * finance_health
        )
        
        # Calculate coupling factor (how well containers sync)
        coupling_factor = self._calculate_coupling_factor(
            sales_health, ops_health, finance_health
        )
        
        # Final Φ_sync
        phi_sync = weighted_health * coupling_factor
        
        return round(phi_sync, 4)
    
    def _calculate_coupling_factor(
        self,
        sales: float,
        ops: float,
        finance: float,
    ) -> float:
        """
        Calculate how well the containers are coupled (synchronized).
        
        High coupling = containers moving together (good)
        Low coupling = containers out of sync (bad)
        
        Uses variance-based calculation: lower variance = better coupling
        """
        scores = [sales, ops, finance]
        mean = sum(scores) / len(scores)
        
        # Calculate variance
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        
        # Convert variance to coupling factor (0 variance = 1.0 coupling)
        # Max variance is 0.25 (when one is 0 and others are 1)
        coupling = 1.0 - (variance * 4)  # Scale variance to 0-1
        
        return max(0.5, min(1.0, coupling))  # Clamp between 0.5 and 1.0
    
    def get_snapshot(self) -> CoherenceSnapshot:
        """Get a snapshot of current system coherence."""
        phi_sync = self.calculate_phi_sync()
        
        container_scores = {
            "sales": self.sales.calculate_health(),
            "operations": self.ops.calculate_health(),
            "finance": self.finance.calculate_health(),
        }
        
        coupling_factor = self._calculate_coupling_factor(
            container_scores["sales"],
            container_scores["operations"],
            container_scores["finance"],
        )
        
        recommendation = self._get_recommendation(phi_sync)
        
        snapshot = CoherenceSnapshot(
            phi_sync=phi_sync,
            timestamp=datetime.now(),
            container_scores=container_scores,
            coupling_factor=coupling_factor,
            recommendation=recommendation,
        )
        
        self.history.append(snapshot)
        return snapshot
    
    def _get_recommendation(self, phi_sync: float) -> str:
        """Get operational recommendation based on Φ_sync level."""
        if phi_sync >= self.PRODUCTION_READY:
            return "SCALE AGGRESSIVELY - System optimal"
        elif phi_sync >= self.MACHINE_COMPLETE:
            return "SCALE STEADILY - Machine complete"
        elif phi_sync >= self.OPS_LIVE:
            return "CONTINUE - Ops container live"
        elif phi_sync >= self.SALES_LIVE:
            return "CONTINUE - Sales container live"
        elif phi_sync >= self.FACTORY_BUILT:
            return "BUILD LAYERS - Factory complete"
        elif phi_sync >= self.BASELINE:
            return "BUILD ENGINES - Infrastructure ready"
        else:
            return "PAUSE - Fix infrastructure"
    
    def get_status_display(self) -> str:
        """Get a formatted status display for terminal output."""
        snapshot = self.get_snapshot()
        
        # Determine status emoji
        if snapshot.phi_sync >= self.PRODUCTION_READY:
            status = "🚀"
        elif snapshot.phi_sync >= self.MACHINE_COMPLETE:
            status = "✅"
        elif snapshot.phi_sync >= self.OPS_LIVE:
            status = "🔧"
        elif snapshot.phi_sync >= self.SALES_LIVE:
            status = "📈"
        elif snapshot.phi_sync >= self.FACTORY_BUILT:
            status = "🏭"
        elif snapshot.phi_sync >= self.BASELINE:
            status = "🔨"
        else:
            status = "⚠️"
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║  CEP COHERENCE METRICS                                       ║
╠══════════════════════════════════════════════════════════════╣
║  Φ_sync: {snapshot.phi_sync:.4f}  {status}                                      
║                                                              ║
║  Container Health:                                           ║
║    Sales:      {snapshot.container_scores['sales']:.2f}                                         
║    Operations: {snapshot.container_scores['operations']:.2f}                                         
║    Finance:    {snapshot.container_scores['finance']:.2f}                                         
║                                                              ║
║  Coupling Factor: {snapshot.coupling_factor:.2f}                                    
║                                                              ║
║  Status: {snapshot.recommendation:<50}║
╚══════════════════════════════════════════════════════════════╝
"""
    
    def check_red_flags(self) -> List[str]:
        """Check for system red flags that require attention."""
        flags = []
        phi_sync = self.calculate_phi_sync()
        
        if phi_sync < 0.85:
            flags.append(f"CRITICAL: Φ_sync ({phi_sync:.2f}) below 0.85 - PAUSE and fix system")
        
        if self.sales.metrics.error_rate > 0.10:
            flags.append(f"Sales error rate ({self.sales.metrics.error_rate:.1%}) above 10%")
        
        if self.ops.metrics.error_rate > 0.10:
            flags.append(f"Ops error rate ({self.ops.metrics.error_rate:.1%}) above 10%")
        
        if self.finance.metrics.error_rate > 0.05:
            flags.append(f"Finance error rate ({self.finance.metrics.error_rate:.1%}) above 5%")
        
        # Check for container imbalance
        scores = [
            self.sales.calculate_health(),
            self.ops.calculate_health(),
            self.finance.calculate_health(),
        ]
        max_diff = max(scores) - min(scores)
        if max_diff > 0.30:
            flags.append(f"Container imbalance detected (diff: {max_diff:.2f})")
        
        return flags
    
    def simulate_layer_completion(self, layer_number: int) -> float:
        """
        Simulate the Φ_sync improvement from completing a layer.
        
        Each layer adds approximately 0.05-0.08 to Φ_sync.
        """
        # Base improvement per layer
        base_improvement = 0.06
        
        # Early layers have more impact
        if layer_number <= 3:
            improvement = base_improvement * 1.2
        elif layer_number <= 6:
            improvement = base_improvement * 1.0
        else:
            improvement = base_improvement * 0.8
        
        current = self.calculate_phi_sync()
        projected = min(1.0, current + improvement)
        
        return projected
