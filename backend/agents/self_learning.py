"""
Self-Learning Agent - Layer 9
Machine learning agent for continuous improvement and optimization
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime, timedelta
import json
import numpy as np
from collections import defaultdict

# CopilotKit imports
from deepagents import create_deep_agent, DeepAgent
from copilotkit.langchain import copilotkit_emit_state

# CEP Machine imports
from cep_machine.layers.feedback_loop import FeedbackLoop
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class SelfLearningAgent:
    """Agent for continuous learning and system optimization"""
    
    def __init__(self):
        self.feedback_loop = FeedbackLoop()
        self.db = get_database()
        self.cache = get_cache()
        
        # Learning parameters
        self.learning_rate = 0.01
        self.pattern_threshold = 0.7
        self.optimization_frequency = timedelta(days=7)
    
    async def analyze_performance(self, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across all layers to identify patterns"""
        # Get performance data from all layers
        time_range = analysis_config.get("time_range", "30d")
        
        # Collect metrics from each layer
        layer_metrics = {}
        
        # Layer 1: Prospect Research
        layer_metrics["prospect_research"] = await self._get_prospect_metrics(time_range)
        
        # Layer 2: Pitch Generator
        layer_metrics["pitch_generator"] = await self._get_pitch_metrics(time_range)
        
        # Layer 3: Outreach Engine
        layer_metrics["outreach_engine"] = await self._get_outreach_metrics(time_range)
        
        # Layer 4: Booking Handler
        layer_metrics["booking_handler"] = await self._get_booking_metrics(time_range)
        
        # Layer 5: Onboarding Flow
        layer_metrics["onboarding_flow"] = await self._get_onboarding_metrics(time_range)
        
        # Layer 6: GBP Optimizer
        layer_metrics["gbp_optimizer"] = await self._get_gbp_metrics(time_range)
        
        # Layer 7: Reporting Engine
        layer_metrics["reporting_engine"] = await self._get_reporting_metrics(time_range)
        
        # Layer 8: Finance Tracker
        layer_metrics["finance_tracker"] = await self._get_finance_metrics(time_range)
        
        # Identify patterns
        patterns = await self._identify_patterns(layer_metrics)
        
        # Generate insights
        insights = await self._generate_performance_insights(layer_metrics, patterns)
        
        # Store analysis
        analysis = {
            "id": f"analysis_{datetime.now().timestamp()}",
            "time_range": time_range,
            "layer_metrics": layer_metrics,
            "patterns": patterns,
            "insights": insights,
            "analyzed_at": datetime.now().isoformat()
        }
        
        await self.db.create("performance_analyses", analysis)
        
        # Emit state for real-time monitoring
        await copilotkit_emit_state(
            {
                "type": "performance_analysis_completed",
                "data": analysis
            },
            {"channel": "learning_updates"}
        )
        
        return analysis
    
    async def test_hypotheses(self, hypothesis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test optimization hypotheses through A/B testing"""
        hypotheses = hypothesis_config.get("hypotheses", [])
        test_duration = hypothesis_config.get("duration_days", 14)
        
        test_results = []
        
        for hypothesis in hypotheses:
            # Create A/B test
            test = await self._create_ab_test(hypothesis, test_duration)
            
            # Run test simulation (in production, this would be real)
            results = await self._simulate_ab_test(test)
            
            # Analyze results
            analysis = await self._analyze_test_results(test, results)
            
            test_results.append({
                "hypothesis": hypothesis,
                "test_id": test["id"],
                "results": results,
                "analysis": analysis,
                "recommendation": "implement" if analysis["significance"] > 0.95 else "reject"
            })
        
        # Store test results
        await self.db.create("ab_test_results", {
            "tests": test_results,
            "conducted_at": datetime.now().isoformat()
        })
        
        return {
            "status": "tests_completed",
            "results": test_results,
            "summary": await self._summarize_test_results(test_results)
        }
    
    async def update_strategies(self, strategy_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent strategies based on learning outcomes"""
        updates = []
        
        for layer, strategies in strategy_updates.items():
            for strategy in strategies:
                # Validate strategy
                validation = await self._validate_strategy(strategy)
                
                if validation["valid"]:
                    # Apply strategy update
                    update_result = await self._apply_strategy_update(layer, strategy)
                    
                    updates.append({
                        "layer": layer,
                        "strategy": strategy["name"],
                        "applied": True,
                        "result": update_result
                    })
                    
                    # Track strategy performance
                    await self._track_strategy_performance(layer, strategy)
                else:
                    updates.append({
                        "layer": layer,
                        "strategy": strategy["name"],
                        "applied": False,
                        "reason": validation["errors"]
                    })
        
        # Store updates
        await self.db.create("strategy_updates", {
            "updates": updates,
            "applied_at": datetime.now().isoformat()
        })
        
        # Emit strategy update notification
        await copilotkit_emit_state(
            {
                "type": "strategies_updated",
                "data": {"updates": updates}
            },
            {"channel": "learning_updates"}
        )
        
        return {
            "status": "strategies_updated",
            "updates": updates,
            "success_rate": sum(1 for u in updates if u["applied"]) / len(updates)
        }
    
    async def monitor_impact(self, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor the impact of implemented optimizations"""
        # Get recent changes
        recent_changes = await self._get_recent_changes(days=7)
        
        # Measure impact metrics
        impact_metrics = {}
        
        for change in recent_changes:
            # Get before/after metrics
            before_metrics = await self._get_metrics_before_change(change)
            after_metrics = await self._get_metrics_after_change(change)
            
            # Calculate impact
            impact = await self._calculate_change_impact(before_metrics, after_metrics)
            
            impact_metrics[change["id"]] = {
                "change": change,
                "before": before_metrics,
                "after": after_metrics,
                "impact": impact,
                "roi": await self._calculate_roi(change, impact)
            }
        
        # Generate impact summary
        summary = await self._generate_impact_summary(impact_metrics)
        
        # Store monitoring results
        await self.db.create("impact_monitoring", {
            "metrics": impact_metrics,
            "summary": summary,
            "monitored_at": datetime.now().isoformat()
        })
        
        return {
            "status": "impact_monitored",
            "metrics": impact_metrics,
            "summary": summary
        }
    
    # Helper methods
    async def _get_prospect_metrics(self, time_range: str) -> Dict:
        """Get prospect research layer metrics"""
        # Mock implementation - fetch from database
        return {
            "prospects_generated": 150,
            "conversion_rate": 0.167,
            "quality_score": 0.82,
            "sources": {
                "website": 0.4,
                "referral": 0.27,
                "cold": 0.2,
                "social": 0.13
            }
        }
    
    async def _get_pitch_metrics(self, time_range: str) -> Dict:
        """Get pitch generator layer metrics"""
        return {
            "pitches_sent": 120,
            "response_rate": 0.35,
            "average_pitch_score": 0.78,
            "personalization_effectiveness": 0.85
        }
    
    async def _get_outreach_metrics(self, time_range: str) -> Dict:
        """Get outreach engine layer metrics"""
        return {
            "outreach_attempts": 500,
            "engagement_rate": 0.25,
            "sequence_completion": 0.60,
            "channel_performance": {
                "email": 0.30,
                "phone": 0.40,
                "linkedin": 0.25,
                "sms": 0.05
            }
        }
    
    async def _get_booking_metrics(self, time_range: str) -> Dict:
        """Get booking handler layer metrics"""
        return {
            "meetings_scheduled": 40,
            "show_rate": 0.875,
            "approval_time_hours": 2.5,
            "calendar_integration_success": 0.95
        }
    
    async def _get_onboarding_metrics(self, time_range: str) -> Dict:
        """Get onboarding flow layer metrics"""
        return {
            "clients_onboarded": 15,
            "onboarding_duration_days": 5.2,
            "satisfaction_score": 4.6,
            "completion_rate": 0.93
        }
    
    async def _get_gbp_metrics(self, time_range: str) -> Dict:
        """Get GBP optimizer layer metrics"""
        return {
            "profile_visibility": 0.85,
            "review_response_rate": 0.90,
            "ranking_improvement": 0.15,
            "engagement_growth": 0.25
        }
    
    async def _get_reporting_metrics(self, time_range: str) -> Dict:
        """Get reporting engine layer metrics"""
        return {
            "reports_generated": 45,
            "dashboard_views": 1200,
            "insights_generated": 180,
            "user_satisfaction": 4.5
        }
    
    async def _get_finance_metrics(self, time_range: str) -> Dict:
        """Get finance tracker layer metrics"""
        return {
            "revenue_growth": 0.18,
            "collection_rate": 0.95,
            "forecast_accuracy": 0.88,
            "cost_efficiency": 0.92
        }
    
    async def _identify_patterns(self, layer_metrics: Dict) -> List[Dict]:
        """Identify patterns across layer metrics"""
        patterns = []
        
        # Pattern 1: High conversion correlation
        if layer_metrics["pitch_generator"]["response_rate"] > 0.3 and \
           layer_metrics["outreach_engine"]["engagement_rate"] > 0.2:
            patterns.append({
                "type": "correlation",
                "description": "High pitch response correlates with outreach engagement",
                "confidence": 0.85,
                "layers": ["pitch_generator", "outreach_engine"]
            })
        
        # Pattern 2: Seasonal trends
        patterns.append({
            "type": "seasonal",
            "description": "Prospect generation increases by 30% in Q1",
            "confidence": 0.75,
            "layers": ["prospect_research"]
        })
        
        # Pattern 3: Performance bottlenecks
        if layer_metrics["booking_handler"]["approval_time_hours"] > 2:
            patterns.append({
                "type": "bottleneck",
                "description": "Booking approval time exceeds 2 hours",
                "confidence": 0.90,
                "layers": ["booking_handler"]
            })
        
        return patterns
    
    async def _generate_performance_insights(self, metrics: Dict, patterns: List[Dict]) -> List[Dict]:
        """Generate insights from metrics and patterns"""
        insights = []
        
        # Overall performance insight
        avg_conversion = metrics["prospect_research"]["conversion_rate"]
        if avg_conversion > 0.15:
            insights.append({
                "type": "positive",
                "title": "Strong Conversion Performance",
                "description": f"Conversion rate of {avg_conversion * 100:.1f}% exceeds industry average",
                "actionable": True
            })
        
        # Pattern-based insights
        for pattern in patterns:
            if pattern["type"] == "bottleneck":
                insights.append({
                    "type": "warning",
                    "title": "Performance Bottleneck Detected",
                    "description": pattern["description"],
                    "actionable": True,
                    "recommendation": "Optimize approval workflow"
                })
        
        return insights
    
    async def _create_ab_test(self, hypothesis: Dict, duration_days: int) -> Dict:
        """Create A/B test configuration"""
        test = {
            "id": f"test_{datetime.now().timestamp()}",
            "hypothesis": hypothesis,
            "duration_days": duration_days,
            "variants": [
                {"name": "control", "weight": 0.5},
                {"name": "variant", "weight": 0.5}
            ],
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=duration_days)).isoformat()
        }
        
        await self.db.create("ab_tests", test)
        return test
    
    async def _simulate_ab_test(self, test: Dict) -> Dict:
        """Simulate A/B test results"""
        # Mock simulation - in production, run real test
        import random
        
        control_conversions = random.randint(20, 30)
        variant_conversions = random.randint(25, 35)
        
        return {
            "control": {
                "participants": 100,
                "conversions": control_conversions,
                "conversion_rate": control_conversions / 100
            },
            "variant": {
                "participants": 100,
                "conversions": variant_conversions,
                "conversion_rate": variant_conversions / 100
            }
        }
    
    async def _analyze_test_results(self, test: Dict, results: Dict) -> Dict:
        """Analyze A/B test results for statistical significance"""
        # Calculate statistical significance (simplified)
        control_rate = results["control"]["conversion_rate"]
        variant_rate = results["variant"]["conversion_rate"]
        
        # Simple significance calculation
        lift = (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
        significance = 0.95 if abs(lift) > 0.1 else 0.5  # Mock significance
        
        return {
            "lift": lift,
            "significance": significance,
            "winner": "variant" if lift > 0 else "control",
            "recommendation": "implement" if significance > 0.95 else "inconclusive"
        }
    
    async def _summarize_test_results(self, test_results: List[Dict]) -> Dict:
        """Summarize all test results"""
        implemented = sum(1 for t in test_results if t["recommendation"] == "implement")
        
        return {
            "total_tests": len(test_results),
            "implemented": implemented,
            "rejected": len(test_results) - implemented,
            "implementation_rate": implemented / len(test_results) if test_results else 0
        }
    
    async def _validate_strategy(self, strategy: Dict) -> Dict:
        """Validate strategy before implementation"""
        errors = []
        
        if not strategy.get("name"):
            errors.append("Strategy name is required")
        
        if not strategy.get("changes"):
            errors.append("Strategy changes are required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _apply_strategy_update(self, layer: str, strategy: Dict) -> Dict:
        """Apply strategy update to specific layer"""
        # Mock implementation - update layer configuration
        update = {
            "layer": layer,
            "strategy": strategy["name"],
            "changes_applied": strategy["changes"],
            "applied_at": datetime.now().isoformat()
        }
        
        await self.db.create("strategy_applications", update)
        
        return update
    
    async def _track_strategy_performance(self, layer: str, strategy: Dict):
        """Track performance of applied strategy"""
        # Create performance tracking record
        tracking = {
            "layer": layer,
            "strategy": strategy["name"],
            "baseline_metrics": await self._get_current_metrics(layer),
            "tracking_start": datetime.now().isoformat()
        }
        
        await self.db.create("strategy_tracking", tracking)
    
    async def _get_current_metrics(self, layer: str) -> Dict:
        """Get current metrics for a layer"""
        # Mock implementation
        return {"metric1": 100, "metric2": 0.85}
    
    async def _get_recent_changes(self, days: int) -> List[Dict]:
        """Get recent changes to monitor"""
        # Mock implementation
        return [
            {
                "id": "change1",
                "type": "strategy_update",
                "layer": "outreach_engine",
                "implemented_at": (datetime.now() - timedelta(days=2)).isoformat()
            }
        ]
    
    async def _get_metrics_before_change(self, change: Dict) -> Dict:
        """Get metrics before change implementation"""
        # Mock implementation
        return {"conversion_rate": 0.15, "engagement": 0.20}
    
    async def _get_metrics_after_change(self, change: Dict) -> Dict:
        """Get metrics after change implementation"""
        # Mock implementation
        return {"conversion_rate": 0.18, "engagement": 0.25}
    
    async def _calculate_change_impact(self, before: Dict, after: Dict) -> Dict:
        """Calculate impact of change"""
        impact = {}
        
        for metric in before:
            if metric in after:
                change = (after[metric] - before[metric]) / before[metric] if before[metric] > 0 else 0
                impact[metric] = {
                    "before": before[metric],
                    "after": after[metric],
                    "change_percent": change * 100,
                    "impact": "positive" if change > 0 else "negative"
                }
        
        return impact
    
    async def _calculate_roi(self, change: Dict, impact: Dict) -> float:
        """Calculate ROI for change"""
        # Mock ROI calculation
        positive_impacts = sum(1 for i in impact.values() if i["impact"] == "positive")
        total_impacts = len(impact)
        
        return (positive_impacts / total_impacts) if total_impacts > 0 else 0
    
    async def _generate_impact_summary(self, impact_metrics: Dict) -> Dict:
        """Generate summary of all impacts"""
        total_changes = len(impact_metrics)
        positive_changes = sum(
            1 for m in impact_metrics.values()
            if m["roi"] > 0.5
        )
        
        return {
            "total_changes": total_changes,
            "positive_changes": positive_changes,
            "success_rate": positive_changes / total_changes if total_changes > 0 else 0,
            "average_roi": sum(m["roi"] for m in impact_metrics.values()) / total_changes if total_changes > 0 else 0
        }

# Create the self-learning agent
def create_self_learning_agent() -> DeepAgent:
    """Create and configure the self-learning agent"""
    
    agent = create_deep_agent(
        name="self_learning",
        model="openai:gpt-4-turbo-preview",
        system_prompt="""You are a Self-Learning Agent responsible for:
        1. Analyzing performance across all CEP Machine layers
        2. Identifying patterns and optimization opportunities
        3. Testing hypotheses through A/B testing
        4. Updating strategies based on learning outcomes
        5. Monitoring the impact of implemented changes
        
        Always use data-driven insights and statistical validation.""",
        tools=[
            {
                "name": "analyze_performance",
                "description": "Analyze performance and identify patterns",
                "parameters": {
                    "analysis_config": "object"
                }
            },
            {
                "name": "test_hypotheses",
                "description": "Test optimization hypotheses",
                "parameters": {
                    "hypothesis_config": "object"
                }
            },
            {
                "name": "update_strategies",
                "description": "Update agent strategies",
                "parameters": {
                    "strategy_updates": "object"
                }
            },
            {
                "name": "monitor_impact",
                "description": "Monitor impact of changes",
                "parameters": {
                    "monitoring_config": "object"
                }
            }
        ]
    )
    
    # Initialize the agent with our handler
    handler = SelfLearningAgent()
    
    # Register tool handlers
    async def analyze_performance_tool(analysis_config: Dict[str, Any]):
        return await handler.analyze_performance(analysis_config)
    
    async def test_hypotheses_tool(hypothesis_config: Dict[str, Any]):
        return await handler.test_hypotheses(hypothesis_config)
    
    async def update_strategies_tool(strategy_updates: Dict[str, Any]):
        return await handler.update_strategies(strategy_updates)
    
    async def monitor_impact_tool(monitoring_config: Dict[str, Any]):
        return await handler.monitor_impact(monitoring_config)
    
    agent.register_tool("analyze_performance", analyze_performance_tool)
    agent.register_tool("test_hypotheses", test_hypotheses_tool)
    agent.register_tool("update_strategies", update_strategies_tool)
    agent.register_tool("monitor_impact", monitor_impact_tool)
    
    return agent

# Export the agent creation function
__all__ = ["create_self_learning_agent", "SelfLearningAgent"]
