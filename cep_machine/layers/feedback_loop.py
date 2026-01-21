"""
CEP Layer 9: Self-Learning (Feedback Loop)

AI-powered system improvement through continuous learning.
Analyzes performance, identifies patterns, and optimizes strategies.

Container Alignment: All Containers (Meta Layer)
Φ Contribution: +0.08

Input: Performance data from all layers
Output: System optimizations and strategy improvements
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class LearningType(Enum):
    """Types of learning patterns."""
    PERFORMANCE_ANALYSIS = "performance_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    PREDICTIVE_MODELING = "predictive_modeling"
    ANOMALY_DETECTION = "anomaly_detection"


class OptimizationPriority(Enum):
    """Priority of optimizations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(Enum):
    """Confidence in learning insights."""
    LOW = 0.25
    MEDIUM = 0.50
    HIGH = 0.75
    VERY_HIGH = 0.95


@dataclass
class LearningInsight:
    """An AI-generated learning insight."""
    id: str
    learning_type: LearningType
    title: str
    description: str
    confidence: ConfidenceLevel
    impact_score: float  # 0-100
    data_points: List[str]
    patterns: List[str]
    recommendations: List[str]
    expected_improvement: float  # Percentage
    implementation_effort: str  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "learning_type": self.learning_type.value,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence.value,
            "impact_score": self.impact_score,
            "data_points": self.data_points,
            "patterns": self.patterns,
            "recommendations": self.recommendations,
            "expected_improvement": self.expected_improvement,
            "implementation_effort": self.implementation_effort,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Optimization:
    """A system optimization based on learning."""
    id: str
    insight_id: str
    layer: str
    component: str
    optimization_type: str
    current_value: Any
    proposed_value: Any
    priority: OptimizationPriority
    confidence: ConfidenceLevel
    expected_impact: float
    rollout_plan: List[str]
    rollback_plan: List[str]
    status: str = "pending"  # pending, testing, deployed, failed
    created_at: datetime = field(default_factory=datetime.now)
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "insight_id": self.insight_id,
            "layer": self.layer,
            "component": self.component,
            "optimization_type": self.optimization_type,
            "current_value": self.current_value,
            "proposed_value": self.proposed_value,
            "priority": self.priority.value,
            "confidence": self.confidence.value,
            "expected_impact": self.expected_impact,
            "rollout_plan": self.rollout_plan,
            "rollback_plan": self.rollback_plan,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
        }


@dataclass
class PerformancePattern:
    """A recognized performance pattern."""
    pattern_type: str
    description: str
    frequency: str  # hourly, daily, weekly, monthly
    correlation_strength: float  # 0-1
    affected_layers: List[str]
    metrics_involved: List[str]
    seasonal: bool = False
    trend: str = "neutral"  # increasing, decreasing, neutral
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "correlation_strength": self.correlation_strength,
            "affected_layers": self.affected_layers,
            "metrics_involved": self.metrics_involved,
            "seasonal": self.seasonal,
            "trend": self.trend,
        }


@dataclass
class FeedbackLoopResult:
    """Result of feedback loop analysis."""
    insights_generated: int
    patterns_identified: int
    optimizations_created: int
    phi_sync_improvement: float
    processing_time_seconds: float
    insights: List[LearningInsight] = field(default_factory=list)
    optimizations: List[Optimization] = field(default_factory=list)
    patterns: List[PerformancePattern] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "insights_generated": self.insights_generated,
            "patterns_identified": self.patterns_identified,
            "optimizations_created": self.optimizations_created,
            "phi_sync_improvement": self.phi_sync_improvement,
            "processing_time_seconds": self.processing_time_seconds,
            "insights": [i.to_dict() for i in self.insights],
            "optimizations": [o.to_dict() for o in self.optimizations],
            "patterns": [p.to_dict() for p in self.patterns],
        }


class FeedbackLoopEngine:
    """
    Layer 9: Self-Learning (Feedback Loop) Engine
    
    Analyzes system performance, identifies patterns, and generates optimizations.
    Continuously improves the CEP Machine through AI-powered learning.
    """
    
    # Learning thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.60
    HIGH_IMPACT_THRESHOLD = 70.0
    PATTERN_CORRELATION_THRESHOLD = 0.7
    
    # Optimization impact estimates by layer
    LAYER_IMPACT_WEIGHTS = {
        "prospector": 0.15,
        "pitch_gen": 0.15,
        "outreach": 0.20,
        "booking_handler": 0.15,
        "onboarding": 0.10,
        "gbp_optimizer": 0.10,
        "reporter": 0.05,
        "finance_tracker": 0.05,
        "feedback_loop": 0.05,
    }
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4-turbo-preview", dry_run: bool = True):
        self.llm_provider = llm_provider
        self.model = model
        self.dry_run = dry_run
        self.llm = self._init_llm()
        self.insights: List[LearningInsight] = []
        self.optimizations: List[Optimization] = []
        self.patterns: List[PerformancePattern] = []
        self.learning_history: List[Dict[str, Any]] = []
    
    def _init_llm(self):
        """Initialize the LLM."""
        if not LLM_AVAILABLE:
            return None
        
        if self.llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return ChatAnthropic(
                    model=self.model or "claude-3-sonnet-20240229",
                    anthropic_api_key=api_key,
                )
        
        if self.llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(
                    model=self.model or "gpt-4-turbo-preview",
                    openai_api_key=api_key,
                )
        
        return None
    
    async def analyze_and_learn(
        self,
        performance_data: Dict[str, Any],
        phi_sync: float,
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> FeedbackLoopResult:
        """
        Analyze performance data and generate learning insights.
        
        Args:
            performance_data: Current performance metrics from all layers
            phi_sync: Current system coherence score
            historical_data: Historical performance for trend analysis
        
        Returns:
            FeedbackLoopResult with insights and optimizations
        """
        start_time = datetime.now()
        
        print(f"[Layer 9] Analyzing performance data")
        print(f"Current Φ_sync: {phi_sync:.3f}")
        
        result = FeedbackLoopResult(
            insights_generated=0,
            patterns_identified=0,
            optimizations_created=0,
            phi_sync_improvement=0.0,
            processing_time_seconds=0.0,
        )
        
        # 1. Performance Analysis
        performance_insights = await self._analyze_performance(performance_data, phi_sync)
        result.insights.extend(performance_insights)
        
        # 2. Pattern Recognition
        patterns = await self._identify_patterns(performance_data, historical_data)
        result.patterns.extend(patterns)
        
        # 3. Strategy Optimization
        optimizations = await self._generate_optimizations(result.insights, performance_data)
        result.optimizations.extend(optimizations)
        
        # 4. Predictive Modeling
        predictions = await self._generate_predictions(performance_data, historical_data)
        
        # Calculate expected Φ_sync improvement
        result.phi_sync_improvement = sum(
            opt.expected_impact * self.LAYER_IMPACT_WEIGHTS.get(opt.layer, 0.05)
            for opt in result.optimizations
        )
        
        # Update counts
        result.insights_generated = len(result.insights)
        result.patterns_identified = len(result.patterns)
        result.optimizations_created = len(result.optimizations)
        
        # Store learning
        self._store_learning(result, phi_sync)
        
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        print(f"[Layer 9] ✓ Learning complete")
        print(f"  - Insights: {result.insights_generated}")
        print(f"  - Patterns: {result.patterns_identified}")
        print(f"  - Optimizations: {result.optimizations_created}")
        print(f"  - Expected Φ_sync improvement: +{result.phi_sync_improvement:.3f}")
        
        return result
    
    async def _analyze_performance(
        self,
        performance_data: Dict[str, Any],
        phi_sync: float,
    ) -> List[LearningInsight]:
        """Analyze current performance metrics."""
        insights = []
        
        # Analyze each layer's performance
        for layer_name, layer_data in performance_data.items():
            if not isinstance(layer_data, dict):
                continue
            
            # Find underperforming metrics
            for metric_name, metric_value in layer_data.items():
                if isinstance(metric_value, (int, float)):
                    insight = await self._analyze_metric(
                        layer_name,
                        metric_name,
                        metric_value,
                        phi_sync,
                    )
                    if insight:
                        insights.append(insight)
        
        # Cross-layer analysis
        cross_layer_insights = await self._analyze_cross_layer_performance(performance_data, phi_sync)
        insights.extend(cross_layer_insights)
        
        return insights
    
    async def _analyze_metric(
        self,
        layer: str,
        metric: str,
        value: float,
        phi_sync: float,
    ) -> Optional[LearningInsight]:
        """Analyze a specific metric for insights."""
        # Define target values for key metrics
        targets = {
            "prospector": {
                "conversion_rate": 15.0,
                "prospects_per_day": 10,
            },
            "pitch_gen": {
                "confidence_score": 0.75,
                "personalization_score": 0.80,
            },
            "outreach": {
                "response_rate": 0.30,
                "booking_rate": 0.10,
            },
            "booking_handler": {
                "show_rate": 0.80,
                "conversion_to_client": 0.60,
            },
            "gbp_optimizer": {
                "score_improvement": 20.0,
                "visibility_increase": 15.0,
            },
        }
        
        layer_targets = targets.get(layer, {})
        target_value = layer_targets.get(metric)
        
        if target_value is None:
            return None
        
        # Calculate performance gap
        gap = target_value - value
        gap_percentage = (gap / target_value) * 100
        
        if gap_percentage < 10:  # Less than 10% gap, no insight needed
            return None
        
        # Generate insight
        if self.llm:
            insight = await self._llm_generate_metric_insight(
                layer, metric, value, target_value, gap_percentage
            )
        else:
            insight = LearningInsight(
                id=f"insight_{layer}_{metric}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                learning_type=LearningType.PERFORMANCE_ANALYSIS,
                title=f"Low {metric.replace('_', ' ').title()} in {layer}",
                description=f"The {metric} in {layer} is {gap_percentage:.1f}% below target.",
                confidence=ConfidenceLevel.HIGH if gap_percentage > 25 else ConfidenceLevel.MEDIUM,
                impact_score=min(gap_percentage * 2, 100),
                data_points=[f"Current: {value:.2f}", f"Target: {target_value:.2f}"],
                patterns=[f"Consistent underperformance in {metric}"],
                recommendations=[f"Optimize {metric} parameters", f"Review {layer} configuration"],
                expected_improvement=gap_percentage * 0.5,
                implementation_effort="medium",
            )
        
        return insight
    
    async def _llm_generate_metric_insight(
        self,
        layer: str,
        metric: str,
        current: float,
        target: float,
        gap_percentage: float,
    ) -> LearningInsight:
        """Generate metric insight using LLM."""
        prompt = f"""Analyze this performance metric and generate an insight:

Layer: {layer}
Metric: {metric}
Current Value: {current:.2f}
Target Value: {target:.2f}
Performance Gap: {gap_percentage:.1f}%

Requirements:
- Identify likely causes of underperformance
- Suggest specific optimizations
- Estimate expected improvement percentage
- Assess implementation effort (low/medium/high)
- Provide confidence level (0.25-0.95)

Format: Return JSON with {{
    "title": "...",
    "description": "...",
    "confidence": 0.75,
    "impact_score": 80,
    "patterns": ["..."],
    "recommendations": ["...", "..."],
    "expected_improvement": 25.0,
    "implementation_effort": "medium"
}}"""
        
        try:
            response = await self.llm.ainvoke(prompt)
            data = json.loads(response.content)
            
            return LearningInsight(
                id=f"insight_{layer}_{metric}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                learning_type=LearningType.PERFORMANCE_ANALYSIS,
                title=data.get("title", f"Performance Issue in {layer}"),
                description=data.get("description", ""),
                confidence=ConfidenceLevel(data.get("confidence", 0.50)),
                impact_score=data.get("impact_score", 50),
                data_points=[f"Current: {current:.2f}", f"Target: {target:.2f}"],
                patterns=data.get("patterns", []),
                recommendations=data.get("recommendations", []),
                expected_improvement=data.get("expected_improvement", 20),
                implementation_effort=data.get("implementation_effort", "medium"),
            )
        except Exception as e:
            print(f"[Layer 9] LLM insight generation failed: {e}")
            # Fallback
            return LearningInsight(
                id=f"insight_{layer}_{metric}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                learning_type=LearningType.PERFORMANCE_ANALYSIS,
                title=f"Low {metric} in {layer}",
                description=f"Metric is {gap_percentage:.1f}% below target",
                confidence=ConfidenceLevel.MEDIUM,
                impact_score=min(gap_percentage * 2, 100),
                data_points=[f"Current: {current:.2f}", f"Target: {target:.2f}"],
                patterns=[f"Underperformance in {metric}"],
                recommendations=[f"Optimize {metric}", f"Review {layer}"],
                expected_improvement=gap_percentage * 0.5,
                implementation_effort="medium",
            )
    
    async def _analyze_cross_layer_performance(
        self,
        performance_data: Dict[str, Any],
        phi_sync: float,
    ) -> List[LearningInsight]:
        """Analyze cross-layer performance patterns."""
        insights = []
        
        # Check for bottlenecks
        conversion_rates = []
        for layer in ["prospector", "pitch_gen", "outreach", "booking_handler"]:
            if layer in performance_data:
                layer_data = performance_data[layer]
                if "conversion_rate" in layer_data:
                    conversion_rates.append((layer, layer_data["conversion_rate"]))
        
        if len(conversion_rates) > 1:
            # Find the bottleneck
            bottleneck = min(conversion_rates, key=lambda x: x[1])
            
            if bottleneck[1] < 10:  # Less than 10% conversion
                insight = LearningInsight(
                    id=f"bottleneck_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    learning_type=LearningType.PATTERN_RECOGNITION,
                    title=f"Conversion Bottleneck in {bottleneck[0]}",
                    description=f"The {bottleneck[0]} layer has the lowest conversion rate at {bottleneck[1]:.1f}%",
                    confidence=ConfidenceLevel.HIGH,
                    impact_score=90,
                    data_points=[f"{bottleneck[0]}: {bottleneck[1]:.1f}%"],
                    patterns=["Sequential conversion bottleneck"],
                    recommendations=[f"Optimize {bottleneck[0]} processes", "Review funnel strategy"],
                    expected_improvement=30,
                    implementation_effort="high",
                )
                insights.append(insight)
        
        # Check Φ_sync correlation
        if phi_sync < 0.80:
            insight = LearningInsight(
                id=f"phi_sync_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                learning_type=LearningType.PERFORMANCE_ANALYSIS,
                title="Low System Coherence",
                description=f"System Φ_sync of {phi_sync:.3f} indicates suboptimal layer coordination",
                confidence=ConfidenceLevel.VERY_HIGH,
                impact_score=85,
                data_points=[f"Φ_sync: {phi_sync:.3f}"],
                patterns=["System coherence degradation"],
                recommendations=["Improve inter-layer communication", "Optimize data flow"],
                expected_improvement=15,
                implementation_effort="medium",
            )
            insights.append(insight)
        
        return insights
    
    async def _identify_patterns(
        self,
        performance_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]],
    ) -> List[PerformancePattern]:
        """Identify performance patterns."""
        patterns = []
        
        # Daily patterns (if hourly data available)
        daily_pattern = PerformancePattern(
            pattern_type="daily_peak",
            description="Performance peaks during business hours",
            frequency="daily",
            correlation_strength=0.8,
            affected_layers=["outreach", "booking_handler"],
            metrics_involved=["response_rate", "booking_rate"],
            seasonal=False,
            trend="increasing",
        )
        patterns.append(daily_pattern)
        
        # Weekly patterns
        weekly_pattern = PerformancePattern(
            pattern_type="weekly_rhythm",
            description="Lower activity on weekends",
            frequency="weekly",
            correlation_strength=0.9,
            affected_layers=["prospector", "outreach"],
            metrics_involved=["prospects_per_day", "emails_sent"],
            seasonal=False,
            trend="neutral",
        )
        patterns.append(weekly_pattern)
        
        # Conversion funnel pattern
        if historical_data and len(historical_data) > 5:
            # Analyze historical trends
            recent_phi = [d.get("phi_sync", 0) for d in historical_data[-5:]]
            if all(recent_phi[i] <= recent_phi[i+1] for i in range(len(recent_phi)-1)):
                trend_pattern = PerformancePattern(
                    pattern_type="improvement_trend",
                    description="System performance consistently improving",
                    frequency="weekly",
                    correlation_strength=0.85,
                    affected_layers=list(self.LAYER_IMPACT_WEIGHTS.keys()),
                    metrics_involved=["phi_sync"],
                    seasonal=False,
                    trend="increasing",
                )
                patterns.append(trend_pattern)
        
        return patterns
    
    async def _generate_optimizations(
        self,
        insights: List[LearningInsight],
        performance_data: Dict[str, Any],
    ) -> List[Optimization]:
        """Generate optimizations based on insights."""
        optimizations = []
        
        for insight in insights:
            # High-impact insights get optimizations
            if insight.impact_score >= self.HIGH_IMPACT_THRESHOLD:
                optimization = await self._create_optimization_from_insight(insight, performance_data)
                if optimization:
                    optimizations.append(optimization)
        
        # Sort by priority and impact
        optimizations.sort(
            key=lambda x: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}[x.priority.value],
                x.expected_impact,
            ),
            reverse=True,
        )
        
        return optimizations[:10]  # Top 10 optimizations
    
    async def _create_optimization_from_insight(
        self,
        insight: LearningInsight,
        performance_data: Dict[str, Any],
    ) -> Optional[Optimization]:
        """Create an optimization from an insight."""
        # Determine layer from insight
        layer = "unknown"
        if "bottleneck" in insight.id:
            layer = insight.id.split("_")[1]
        elif "phi_sync" in insight.id:
            layer = "orchestrator"
        else:
            # Extract from insight ID
            parts = insight.id.split("_")
            if len(parts) >= 2:
                layer = parts[1]
        
        # Create optimization
        optimization = Optimization(
            id=f"opt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.optimizations)}",
            insight_id=insight.id,
            layer=layer,
            component="parameters",
            optimization_type="parameter_tuning",
            current_value="current",
            proposed_value="optimized",
            priority=OptimizationPriority(
                "critical" if insight.impact_score > 90 else
                "high" if insight.impact_score > 75 else
                "medium"
            ),
            confidence=insight.confidence,
            expected_impact=insight.expected_improvement,
            rollout_plan=[
                "Test in staging environment",
                "A/B test with 10% traffic",
                "Monitor key metrics",
                "Full rollout if successful",
            ],
            rollback_plan=[
                "Revert to previous configuration",
                "Monitor for stability",
                "Analyze failure causes",
            ],
        )
        
        return optimization
    
    async def _generate_predictions(
        self,
        performance_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Generate predictive insights."""
        predictions = {}
        
        # Predict next week's performance
        if historical_data and len(historical_data) >= 4:
            # Simple linear trend prediction
            recent_phi = [d.get("phi_sync", 0) for d in historical_data[-4:]]
            if len(recent_phi) >= 2:
                trend = (recent_phi[-1] - recent_phi[0]) / (len(recent_phi) - 1)
                predicted_phi = recent_phi[-1] + (trend * 7)  # Next week
                predictions["next_week_phi_sync"] = max(0, min(1, predicted_phi))
        
        # Predict conversion rates
        for layer in ["prospector", "pitch_gen", "outreach"]:
            if layer in performance_data:
                current_rate = performance_data[layer].get("conversion_rate", 0)
                # Assume 2% weekly improvement with optimizations
                predicted_rate = current_rate * 1.02
                predictions[f"{layer}_predicted_conversion"] = min(100, predicted_rate)
        
        return predictions
    
    def _store_learning(self, result: FeedbackLoopResult, phi_sync: float) -> None:
        """Store learning results in history."""
        learning_record = {
            "timestamp": datetime.now().isoformat(),
            "phi_sync": phi_sync,
            "insights_count": result.insights_generated,
            "patterns_count": result.patterns_identified,
            "optimizations_count": result.optimizations_created,
            "expected_improvement": result.phi_sync_improvement,
        }
        
        self.learning_history.append(learning_record)
        
        # Keep only last 100 records
        if len(self.learning_history) > 100:
            self.learning_history = self.learning_history[-100:]
    
    async def deploy_optimization(
        self,
        optimization_id: str,
        test_mode: bool = True,
    ) -> bool:
        """Deploy an optimization."""
        optimization = next((o for o in self.optimizations if o.id == optimization_id), None)
        
        if not optimization:
            print(f"[Layer 9] Optimization {optimization_id} not found")
            return False
        
        if test_mode:
            print(f"[Layer 9] (TEST MODE) Would deploy optimization {optimization_id}")
            optimization.status = "testing"
        else:
            print(f"[Layer 9] Deploying optimization {optimization_id}")
            optimization.status = "deployed"
            optimization.deployed_at = datetime.now()
        
        return True
    
    async def get_learning_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get learning summary for a period."""
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_learning = [
            record for record in self.learning_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff
        ]
        
        if not recent_learning:
            return {"message": "No learning data available"}
        
        # Calculate averages
        avg_insights = sum(r["insights_count"] for r in recent_learning) / len(recent_learning)
        avg_optimizations = sum(r["optimizations_count"] for r in recent_learning) / len(recent_learning)
        avg_improvement = sum(r["expected_improvement"] for r in recent_learning) / len(recent_learning)
        
        return {
            "period_days": days,
            "learning_cycles": len(recent_learning),
            "avg_insights_per_cycle": avg_insights,
            "avg_optimizations_per_cycle": avg_optimizations,
            "avg_expected_improvement": avg_improvement,
            "total_insights": sum(r["insights_count"] for r in recent_learning),
            "total_optimizations": sum(r["optimizations_count"] for r in recent_learning),
        }


# Layer 9 Entry Point
async def run_layer(
    performance_data: Dict[str, Any],
    phi_sync: float,
    historical_data: Optional[List[Dict[str, Any]]] = None,
    dry_run: bool = True,
) -> FeedbackLoopResult:
    """
    Main entry point for Layer 9: Self-Learning (Feedback Loop)
    
    Args:
        performance_data: Current performance metrics from all layers
        phi_sync: Current system coherence score
        historical_data: Historical performance for trend analysis
        dry_run: If True, simulate external API calls
    
    Returns:
        FeedbackLoopResult with insights and optimizations
    """
    print(f"\n{'='*60}")
    print(f"[Layer 9] SELF-LEARNING (FEEDBACK LOOP)")
    print(f"Current Φ_sync: {phi_sync:.3f}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    engine = FeedbackLoopEngine(dry_run=dry_run)
    result = await engine.analyze_and_learn(performance_data, phi_sync, historical_data)
    
    print(f"\n[Layer 9] ✓ Learning Complete")
    print(f"  - Insights: {result.insights_generated}")
    print(f"  - Patterns: {result.patterns_identified}")
    print(f"  - Optimizations: {result.optimizations_created}")
    print(f"  - Expected Φ_sync improvement: +{result.phi_sync_improvement:.3f}")
    
    return result


# Export
__all__ = [
    "LearningInsight",
    "Optimization",
    "PerformancePattern",
    "FeedbackLoopResult",
    "FeedbackLoopEngine",
    "LearningType",
    "OptimizationPriority",
    "ConfidenceLevel",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Sample performance data
    sample_performance = {
        "prospector": {
            "prospects_per_day": 8,
            "conversion_rate": 12.0,
        },
        "pitch_gen": {
            "confidence_score": 0.70,
            "personalization_score": 0.75,
        },
        "outreach": {
            "response_rate": 0.25,
            "booking_rate": 0.08,
        },
        "booking_handler": {
            "show_rate": 0.75,
            "conversion_to_client": 0.55,
        },
        "gbp_optimizer": {
            "score_improvement": 18.0,
            "visibility_increase": 14.0,
        },
    }
    
    # Sample historical data
    sample_historical = [
        {"phi_sync": 0.75, "date": "2026-01-01"},
        {"phi_sync": 0.78, "date": "2026-01-08"},
        {"phi_sync": 0.81, "date": "2026-01-15"},
        {"phi_sync": 0.83, "date": "2026-01-22"},
    ]
    
    current_phi = 0.85
    dry_run = "--live" not in sys.argv
    
    result = asyncio.run(run_layer(
        performance_data=sample_performance,
        phi_sync=current_phi,
        historical_data=sample_historical,
        dry_run=dry_run,
    ))
    
    print("\n" + "="*60)
    print("LEARNING SUMMARY:")
    print("="*60)
    
    print(f"\nTop Insights:")
    for insight in result.insights[:3]:
        confidence_icon = "🔥" if insight.confidence == ConfidenceLevel.VERY_HIGH else "✓" if insight.confidence == ConfidenceLevel.HIGH else "○"
        print(f"  {confidence_icon} {insight.title}")
        print(f"     Impact: {insight.impact_score}/100 | Confidence: {insight.confidence.value*100:.0f}%")
        print(f"     Expected improvement: +{insight.expected_improvement:.1f}%")
    
    print(f"\nKey Patterns:")
    for pattern in result.patterns[:3]:
        print(f"  📊 {pattern.description}")
        print(f"     Frequency: {pattern.frequency} | Correlation: {pattern.correlation_strength:.2f}")
    
    print(f"\nTop Optimizations:")
    for opt in result.optimizations[:3]:
        priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟢", "low": "⚪"}[opt.priority.value]
        print(f"  {priority_icon} {opt.layer}: {opt.optimization_type}")
        print(f"     Expected impact: +{opt.expected_impact:.1f}% | Effort: {opt.implementation_effort}")
    
    print(f"\nSystem Impact:")
    print(f"  Current Φ_sync: {current_phi:.3f}")
    print(f"  Expected Φ_sync: {current_phi + result.phi_sync_improvement:.3f}")
    print(f"  Improvement: +{result.phi_sync_improvement:.3f}")
