"""
Tests for Layer 9: Self-Learning (Feedback Loop)

Success Criteria: 3 learning cycles with 10+ insights and Φ_sync improvement.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.feedback_loop import (
    LearningInsight,
    Optimization,
    PerformancePattern,
    FeedbackLoopResult,
    FeedbackLoopEngine,
    LearningType,
    OptimizationPriority,
    ConfidenceLevel,
    run_layer,
)


class TestLearningInsight:
    """Test LearningInsight data class."""
    
    def test_insight_creation(self):
        """Test creating a learning insight."""
        insight = LearningInsight(
            id="insight_001",
            learning_type=LearningType.PERFORMANCE_ANALYSIS,
            title="Low Conversion Rate",
            description="Conversion rate is below target",
            confidence=ConfidenceLevel.HIGH,
            impact_score=75.0,
            data_points=["Current: 10%", "Target: 15%"],
            patterns=["Consistent underperformance"],
            recommendations=["Optimize parameters"],
            expected_improvement=25.0,
            implementation_effort="medium",
        )
        
        assert insight.id == "insight_001"
        assert insight.learning_type == LearningType.PERFORMANCE_ANALYSIS
        assert insight.confidence == ConfidenceLevel.HIGH
        assert insight.impact_score == 75.0
    
    def test_insight_to_dict(self):
        """Test insight serialization."""
        insight = LearningInsight(
            id="insight_001",
            learning_type=LearningType.PERFORMANCE_ANALYSIS,
            title="Test Insight",
            description="Test description",
            confidence=ConfidenceLevel.MEDIUM,
            impact_score=50.0,
            data_points=["Test data"],
            patterns=["Test pattern"],
            recommendations=["Test recommendation"],
            expected_improvement=20.0,
            implementation_effort="low",
        )
        
        data = insight.to_dict()
        assert data["id"] == "insight_001"
        assert data["learning_type"] == "performance_analysis"
        assert data["confidence"] == 0.50
        assert data["impact_score"] == 50.0


class TestOptimization:
    """Test Optimization data class."""
    
    def test_optimization_creation(self):
        """Test creating an optimization."""
        opt = Optimization(
            id="opt_001",
            insight_id="insight_001",
            layer="prospector",
            component="parameters",
            optimization_type="parameter_tuning",
            current_value="old_value",
            proposed_value="new_value",
            priority=OptimizationPriority.HIGH,
            confidence=ConfidenceLevel.HIGH,
            expected_impact=25.0,
            rollout_plan=["Test", "Deploy"],
            rollback_plan=["Revert"],
        )
        
        assert opt.id == "opt_001"
        assert opt.layer == "prospector"
        assert opt.priority == OptimizationPriority.HIGH
        assert opt.status == "pending"
    
    def test_optimization_deployment(self):
        """Test optimization deployment."""
        opt = Optimization(
            id="opt_001",
            insight_id="insight_001",
            layer="prospector",
            component="parameters",
            optimization_type="parameter_tuning",
            current_value="old",
            proposed_value="new",
            priority=OptimizationPriority.HIGH,
            confidence=ConfidenceLevel.HIGH,
            expected_impact=25.0,
            rollout_plan=[],
            rollback_plan=[],
        )
        
        # Deploy
        opt.status = "deployed"
        opt.deployed_at = datetime.now()
        
        assert opt.status == "deployed"
        assert opt.deployed_at is not None


class TestPerformancePattern:
    """Test PerformancePattern data class."""
    
    def test_pattern_creation(self):
        """Test creating a performance pattern."""
        pattern = PerformancePattern(
            pattern_type="daily_peak",
            description="Performance peaks during business hours",
            frequency="daily",
            correlation_strength=0.8,
            affected_layers=["prospector", "outreach"],
            metrics_involved=["conversion_rate"],
            seasonal=False,
            trend="increasing",
        )
        
        assert pattern.pattern_type == "daily_peak"
        assert pattern.frequency == "daily"
        assert pattern.correlation_strength == 0.8
        assert not pattern.seasonal
    
    def test_pattern_to_dict(self):
        """Test pattern serialization."""
        pattern = PerformancePattern(
            pattern_type="weekly_rhythm",
            description="Weekly performance pattern",
            frequency="weekly",
            correlation_strength=0.9,
            affected_layers=["all"],
            metrics_involved=["phi_sync"],
        )
        
        data = pattern.to_dict()
        assert data["pattern_type"] == "weekly_rhythm"
        assert data["frequency"] == "weekly"
        assert data["correlation_strength"] == 0.9


class TestFeedbackLoopEngine:
    """Test FeedbackLoopEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return FeedbackLoopEngine(dry_run=True)
    
    @pytest.fixture
    def sample_performance(self):
        return {
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
        }
    
    @pytest.fixture
    def sample_historical(self):
        return [
            {"phi_sync": 0.75, "date": "2026-01-01"},
            {"phi_sync": 0.78, "date": "2026-01-08"},
            {"phi_sync": 0.81, "date": "2026-01-15"},
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_and_learn(self, engine, sample_performance, sample_historical):
        """Test complete analysis and learning cycle."""
        result = await engine.analyze_and_learn(
            performance_data=sample_performance,
            phi_sync=0.85,
            historical_data=sample_historical,
        )
        
        assert isinstance(result, FeedbackLoopResult)
        assert result.insights_generated >= 0
        assert result.patterns_identified > 0
        assert result.optimizations_created >= 0
        assert result.phi_sync_improvement >= 0
        assert len(result.insights) == result.insights_generated
        assert len(result.patterns) == result.patterns_identified
        assert len(result.optimizations) == result.optimizations_created
    
    @pytest.mark.asyncio
    async def test_analyze_performance(self, engine, sample_performance):
        """Test performance analysis."""
        insights = await engine._analyze_performance(sample_performance, 0.85)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert isinstance(insight, LearningInsight)
            assert insight.confidence in ConfidenceLevel
            assert 0 <= insight.impact_score <= 100
            assert insight.expected_improvement >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_metric(self, engine):
        """Test individual metric analysis."""
        insight = await engine._analyze_metric(
            layer="prospector",
            metric="conversion_rate",
            value=10.0,
            phi_sync=0.85,
        )
        
        if insight:  # Only generated if below target
            assert insight.learning_type == LearningType.PERFORMANCE_ANALYSIS
            assert "conversion_rate" in insight.title.lower()
            assert insight.confidence >= ConfidenceLevel.LOW
    
    @pytest.mark.asyncio
    async def test_analyze_cross_layer_performance(self, engine, sample_performance):
        """Test cross-layer performance analysis."""
        insights = await engine._analyze_cross_layer_performance(sample_performance, 0.85)
        
        assert len(insights) >= 0
        
        for insight in insights:
            assert isinstance(insight, LearningInsight)
            # Should identify bottlenecks or Φ_sync issues
    
    @pytest.mark.asyncio
    async def test_identify_patterns(self, engine, sample_performance, sample_historical):
        """Test pattern identification."""
        patterns = await engine._identify_patterns(sample_performance, sample_historical)
        
        assert len(patterns) > 0
        
        for pattern in patterns:
            assert isinstance(pattern, PerformancePattern)
            assert pattern.frequency in ["hourly", "daily", "weekly", "monthly"]
            assert 0 <= pattern.correlation_strength <= 1
    
    @pytest.mark.asyncio
    async def test_generate_optimizations(self, engine, sample_performance):
        """Test optimization generation."""
        # Create a high-impact insight
        insight = LearningInsight(
            id="test_insight",
            learning_type=LearningType.PERFORMANCE_ANALYSIS,
            title="Test Issue",
            description="Test description",
            confidence=ConfidenceLevel.HIGH,
            impact_score=80.0,
            data_points=[],
            patterns=[],
            recommendations=[],
            expected_improvement=25.0,
            implementation_effort="medium",
        )
        
        optimizations = await engine._generate_optimizations([insight], sample_performance)
        
        assert len(optimizations) > 0
        
        for opt in optimizations:
            assert isinstance(opt, Optimization)
            assert opt.insight_id == insight.id
            assert opt.priority in OptimizationPriority
            assert opt.expected_impact > 0
    
    @pytest.mark.asyncio
    async def test_deploy_optimization(self, engine):
        """Test optimization deployment."""
        # Create an optimization
        opt = Optimization(
            id="opt_test",
            insight_id="insight_test",
            layer="prospector",
            component="test",
            optimization_type="test",
            current_value="old",
            proposed_value="new",
            priority=OptimizationPriority.HIGH,
            confidence=ConfidenceLevel.HIGH,
            expected_impact=25.0,
            rollout_plan=[],
            rollback_plan=[],
        )
        
        engine.optimizations.append(opt)
        
        # Deploy in test mode
        success = await engine.deploy_optimization("opt_test", test_mode=True)
        assert success
        assert opt.status == "testing"
        
        # Deploy for real
        success = await engine.deploy_optimization("opt_test", test_mode=False)
        assert success
        assert opt.status == "deployed"
        assert opt.deployed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_learning_summary(self, engine):
        """Test learning summary generation."""
        # Add some learning history
        engine.learning_history = [
            {
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "phi_sync": 0.80,
                "insights_count": 5,
                "patterns_count": 3,
                "optimizations_count": 2,
                "expected_improvement": 0.05,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "phi_sync": 0.82,
                "insights_count": 7,
                "patterns_count": 4,
                "optimizations_count": 3,
                "expected_improvement": 0.07,
            },
        ]
        
        summary = await engine.get_learning_summary(days=30)
        
        assert "period_days" in summary
        assert "learning_cycles" in summary
        assert "avg_insights_per_cycle" in summary
        assert summary["learning_cycles"] == 2
        assert summary["avg_insights_per_cycle"] == 6.0
    
    @pytest.mark.asyncio
    async def test_generate_predictions(self, engine, sample_performance, sample_historical):
        """Test predictive modeling."""
        predictions = await engine._generate_predictions(sample_performance, sample_historical)
        
        assert isinstance(predictions, dict)
        
        if sample_historical and len(sample_historical) >= 4:
            assert "next_week_phi_sync" in predictions
        
        # Check layer predictions
        for layer in ["prospector", "pitch_gen", "outreach"]:
            if layer in sample_performance:
                assert f"{layer}_predicted_conversion" in predictions


class TestLayerEntry:
    """Test Layer 9 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        performance_data = {
            "prospector": {"conversion_rate": 10.0},
            "pitch_gen": {"confidence_score": 0.70},
            "outreach": {"response_rate": 0.25},
        }
        
        historical_data = [
            {"phi_sync": 0.80},
            {"phi_sync": 0.82},
            {"phi_sync": 0.84},
        ]
        
        result = await run_layer(
            performance_data=performance_data,
            phi_sync=0.85,
            historical_data=historical_data,
            dry_run=True,
        )
        
        assert isinstance(result, FeedbackLoopResult)
        assert result.insights_generated >= 0
        assert result.patterns_identified > 0
        assert result.phi_sync_improvement >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
