"""
Tests for Layer 6: GBP Optimizer

Success Criteria: 3 test clients optimized with 20+ point GBP score improvement.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.gbp_optimizer import (
    GBPOptimization,
    GBPPost,
    GBPOptimizationResult,
    GBPOptimizerEngine,
    GBPOptimizationType,
    PostType,
    OptimizationStatus,
    run_layer,
)


class TestGBPOptimization:
    """Test GBPOptimization data class."""
    
    def test_optimization_creation(self):
        """Test creating an optimization."""
        opt = GBPOptimization(
            id="opt_001",
            client_id="client_001",
            business_name="Test Business",
            optimization_type=GBPOptimizationType.POST_CREATION,
            title="Create GBP Post",
            description="Create a new post for GBP",
        )
        
        assert opt.id == "opt_001"
        assert opt.optimization_type == GBPOptimizationType.POST_CREATION
        assert opt.status == OptimizationStatus.PENDING
    
    def test_optimization_to_dict(self):
        """Test optimization serialization."""
        opt = GBPOptimization(
            id="opt_001",
            client_id="client_001",
            business_name="Test Business",
            optimization_type=GBPOptimizationType.POST_CREATION,
            title="Create GBP Post",
            description="Create a new post for GBP",
            completed_at=datetime.now(),
        )
        
        data = opt.to_dict()
        assert data["id"] == "opt_001"
        assert data["optimization_type"] == "post_creation"
        assert data["status"] == "pending"
        assert data["completed_at"] is not None


class TestGBPPost:
    """Test GBPPost data class."""
    
    def test_post_creation(self):
        """Test creating a GBP post."""
        post = GBPPost(
            id="post_001",
            client_id="client_001",
            business_name="Test Business",
            post_type=PostType.UPDATE,
            title="Business Update",
            content="We're excited to share...",
            call_to_action="Call us today!",
        )
        
        assert post.id == "post_001"
        assert post.post_type == PostType.UPDATE
        assert post.status == OptimizationStatus.PENDING
    
    def test_post_scheduling(self):
        """Test post scheduling."""
        scheduled_time = datetime.now() + timedelta(days=1)
        post = GBPPost(
            id="post_001",
            client_id="client_001",
            business_name="Test Business",
            post_type=PostType.UPDATE,
            title="Business Update",
            content="We're excited to share...",
            call_to_action="Call us today!",
            scheduled_at=scheduled_time,
        )
        
        assert post.scheduled_at == scheduled_time
        assert post.status == OptimizationStatus.SCHEDULED


class TestGBPOptimizerEngine:
    """Test GBPOptimizerEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return GBPOptimizerEngine(dry_run=True)
    
    @pytest.mark.asyncio
    async def test_optimize_gbp(self, engine):
        """Test complete GBP optimization."""
        result = await engine.optimize_gbp(
            client_id="client_001",
            business_name="Test Dental",
            business_type="dental",
            current_gbp_score=45.0,
        )
        
        assert isinstance(result, GBPOptimizationResult)
        assert result.client_id == "client_001"
        assert result.business_name == "Test Dental"
        assert result.optimizations_completed > 0
        assert result.posts_created > 0
        assert result.score_improvement > 0
    
    @pytest.mark.asyncio
    async def test_optimization_types(self, engine):
        """Test different optimization types."""
        result = await engine.optimize_gbp(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            current_gbp_score=45.0,
            optimization_types=[GBPOptimizationType.POST_CREATION],
        )
        
        assert result.optimizations_completed == 1
        assert result.posts_created >= 1
        
        opt = result.optimizations[0]
        assert opt.optimization_type == GBPOptimizationType.POST_CREATION
        assert opt.status == OptimizationStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_business_type_content(self, engine):
        """Test content varies by business type."""
        # Dental
        dental_result = await engine.optimize_gbp(
            client_id="client_dental",
            business_name="Test Dental",
            business_type="dental",
            current_gbp_score=45.0,
        )
        
        # HVAC
        hvac_result = await engine.optimize_gbp(
            client_id="client_hvac",
            business_name="Test HVAC",
            business_type="hvac",
            current_gbp_score=45.0,
        )
        
        # Check different post frequencies
        assert dental_result.posts_created != hvac_result.posts_created
    
    @pytest.mark.asyncio
    async def test_content_calendar(self, engine):
        """Test content calendar creation."""
        posts = await engine._create_content_calendar(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
        )
        
        assert len(posts) > 0
        assert all(p.client_id == "client_001" for p in posts)
        assert all(p.scheduled_at > datetime.now() for p in posts)
        
        # Check posts are spread out
        dates = [p.scheduled_at.date() for p in posts]
        unique_dates = set(dates)
        assert len(unique_dates) > 1  # Posts on different days
    
    @pytest.mark.asyncio
    async def test_profile_completion(self, engine):
        """Test profile completion optimization."""
        opt = await engine._run_optimization(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            opt_type=GBPOptimizationType.PROFILE_COMPLETION,
        )
        
        assert opt.optimization_type == GBPOptimizationType.PROFILE_COMPLETION
        assert opt.status == OptimizationStatus.COMPLETED
        assert opt.content is not None
    
    @pytest.mark.asyncio
    async def test_photo_upload(self, engine):
        """Test photo upload optimization."""
        opt = await engine._run_optimization(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            opt_type=GBPOptimizationType.PHOTO_UPLOAD,
        )
        
        assert opt.optimization_type == GBPOptimizationType.PHOTO_UPLOAD
        assert opt.status == OptimizationStatus.COMPLETED
        assert len(opt.media_urls) > 0
    
    @pytest.mark.asyncio
    async def test_review_response(self, engine):
        """Test review response optimization."""
        opt = await engine._run_optimization(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            opt_type=GBPOptimizationType.REVIEW_RESPONSE,
        )
        
        assert opt.optimization_type == GBPOptimizationType.REVIEW_RESPONSE
        assert opt.status == OptimizationStatus.COMPLETED
        assert "responses" in opt.metadata
    
    @pytest.mark.asyncio
    async def test_qa_management(self, engine):
        """Test Q&A management optimization."""
        opt = await engine._run_optimization(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            opt_type=GBPOptimizationType.Q&A_MANAGEMENT,
        )
        
        assert opt.optimization_type == GBPOptimizationType.Q&A_MANAGEMENT
        assert opt.status == OptimizationStatus.COMPLETED
        assert "qa_pairs" in opt.metadata
        assert len(opt.metadata["qa_pairs"]) > 0
    
    @pytest.mark.asyncio
    async def test_score_improvement(self, engine):
        """Test score improvement calculation."""
        initial_score = 45.0
        
        result = await engine.optimize_gbp(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            current_gbp_score=initial_score,
        )
        
        expected_improvement = result.optimizations_completed * 5
        assert result.score_improvement == expected_improvement
        assert initial_score + result.score_improvement <= 100
    
    @pytest.mark.asyncio
    async def test_get_optimization_report(self, engine):
        """Test optimization report generation."""
        # Run optimization first
        await engine.optimize_gbp(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            current_gbp_score=45.0,
        )
        
        # Get report
        report = await engine.get_optimization_report("client_001", days=30)
        
        assert report["client_id"] == "client_001"
        assert report["period_days"] == 30
        assert report["optimizations_completed"] > 0
        assert "optimization_types" in report


class TestLayerEntry:
    """Test Layer 6 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        result = await run_layer(
            client_id="client_001",
            business_name="Test Business",
            business_type="dental",
            current_gbp_score=45.0,
            dry_run=True,
        )
        
        assert isinstance(result, GBPOptimizationResult)
        assert result.client_id == "client_001"
        assert result.business_name == "Test Business"
        assert result.optimizations_completed > 0
        assert result.score_improvement > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
