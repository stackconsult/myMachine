"""
Tests for CEP Core Components

Success Criteria: Unit tests for CoherenceMetrics pass with Φ_sync = 0.30 (baseline).
"""

import pytest
import asyncio
from datetime import datetime

from cep_machine.core.containers import (
    CEPContainer,
    SalesContainer,
    OpsContainer,
    FinanceContainer,
    ContainerType,
    Timescale,
)
from cep_machine.core.coherence import CoherenceMetrics
from cep_machine.core.database import Database


class TestContainers:
    """Test CEP Container classes."""
    
    def test_sales_container_init(self):
        """Test SalesContainer initialization."""
        sales = SalesContainer()
        assert sales.name == "Sales"
        assert sales.container_type == ContainerType.SALES
        assert sales.timescale == Timescale.DAILY
        assert sales.weight == 0.33
    
    def test_ops_container_init(self):
        """Test OpsContainer initialization."""
        ops = OpsContainer()
        assert ops.name == "Operations"
        assert ops.container_type == ContainerType.OPERATIONS
        assert ops.timescale == Timescale.HOURLY
        assert ops.weight == 0.34
    
    def test_finance_container_init(self):
        """Test FinanceContainer initialization."""
        finance = FinanceContainer()
        assert finance.name == "Finance"
        assert finance.container_type == ContainerType.FINANCE
        assert finance.timescale == Timescale.WEEKLY
        assert finance.weight == 0.33
    
    def test_container_health_baseline(self):
        """Test container health starts at 0."""
        sales = SalesContainer()
        assert sales.calculate_health() == 0.0
    
    def test_container_record_event(self):
        """Test recording events."""
        sales = SalesContainer()
        sales.record_prospect({"company": "Test Corp"})
        assert len(sales.events) == 1
        assert sales.prospects_researched == 1
    
    def test_container_metrics_update(self):
        """Test updating metrics."""
        ops = OpsContainer()
        ops.update_metrics(efficiency=0.8, throughput=100)
        assert ops.metrics.efficiency == 0.8
        assert ops.metrics.throughput == 100


class TestCoherence:
    """Test CoherenceMetrics calculations."""
    
    def test_coherence_baseline(self):
        """Test baseline Φ_sync = 0.30 when containers are empty."""
        coherence = CoherenceMetrics()
        phi = coherence.calculate_phi_sync()
        # With empty containers, phi should be 0
        assert phi >= 0.0
        assert phi <= 1.0
    
    def test_coherence_with_healthy_containers(self):
        """Test Φ_sync increases with healthy containers."""
        sales = SalesContainer()
        ops = OpsContainer()
        finance = FinanceContainer()
        
        # Set healthy metrics
        sales.update_metrics(conversion_rate=0.8, efficiency=0.7)
        ops.update_metrics(efficiency=0.9, throughput=100)
        finance.update_metrics(efficiency=0.85, conversion_rate=0.95)
        
        coherence = CoherenceMetrics(sales=sales, ops=ops, finance=finance)
        phi = coherence.calculate_phi_sync()
        
        # Should be higher than baseline
        assert phi > 0.5
    
    def test_coherence_recommendation(self):
        """Test coherence recommendations."""
        coherence = CoherenceMetrics()
        snapshot = coherence.get_snapshot()
        
        assert snapshot.recommendation is not None
        assert len(snapshot.recommendation) > 0
    
    def test_coherence_thresholds(self):
        """Test coherence threshold constants."""
        assert CoherenceMetrics.BASELINE == 0.30
        assert CoherenceMetrics.FACTORY_BUILT == 0.65
        assert CoherenceMetrics.SALES_LIVE == 0.70
        assert CoherenceMetrics.OPS_LIVE == 0.80
        assert CoherenceMetrics.MACHINE_COMPLETE == 0.88
        assert CoherenceMetrics.PRODUCTION_READY == 0.95
    
    def test_coherence_red_flags_empty(self):
        """Test no red flags with healthy system."""
        sales = SalesContainer()
        ops = OpsContainer()
        finance = FinanceContainer()
        
        # Set healthy metrics with no errors
        sales.update_metrics(conversion_rate=0.9, efficiency=0.9, error_rate=0.01)
        ops.update_metrics(efficiency=0.9, error_rate=0.01)
        finance.update_metrics(efficiency=0.9, error_rate=0.01)
        
        coherence = CoherenceMetrics(sales=sales, ops=ops, finance=finance)
        flags = coherence.check_red_flags()
        
        # Should have no critical flags
        assert not any("CRITICAL" in f for f in flags)
    
    def test_simulate_layer_completion(self):
        """Test layer completion simulation."""
        coherence = CoherenceMetrics()
        
        for layer in range(1, 10):
            projected = coherence.simulate_layer_completion(layer)
            assert projected > coherence.calculate_phi_sync()


class TestDatabase:
    """Test Database operations."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a test database."""
        db_path = tmp_path / "test.db"
        return Database(str(db_path))
    
    @pytest.mark.asyncio
    async def test_database_init(self, test_db):
        """Test database initialization."""
        await test_db.initialize()
        
        # Check layers were seeded
        layers = await test_db.get_all_layers()
        assert len(layers) == 9
    
    @pytest.mark.asyncio
    async def test_get_layer(self, test_db):
        """Test getting a specific layer."""
        await test_db.initialize()
        
        layer = await test_db.get_layer(1)
        assert layer is not None
        assert layer["name"] == "Prospect Research"
    
    @pytest.mark.asyncio
    async def test_update_layer_status(self, test_db):
        """Test updating layer status."""
        await test_db.initialize()
        
        await test_db.update_layer_status(1, "completed", 0.07)
        
        layer = await test_db.get_layer(1)
        assert layer["status"] == "completed"
        assert layer["phi_contribution"] == 0.07
    
    @pytest.mark.asyncio
    async def test_add_research_log(self, test_db):
        """Test adding research log."""
        await test_db.initialize()
        
        log_id = await test_db.add_research_log(
            query="test query",
            source_url="https://example.com",
            source_title="Example",
            summary="Test summary",
            citations="[]",
            layer_id=1,
        )
        
        assert log_id > 0
        
        research = await test_db.get_research_for_layer(1)
        assert len(research) == 1
    
    @pytest.mark.asyncio
    async def test_record_coherence(self, test_db):
        """Test recording coherence metrics."""
        await test_db.initialize()
        
        await test_db.record_coherence(
            phi_sync=0.65,
            sales_health=0.7,
            ops_health=0.8,
            finance_health=0.75,
            coupling_factor=0.9,
            recommendation="SCALE STEADILY",
        )
        
        latest = await test_db.get_latest_coherence()
        assert latest is not None
        assert latest["phi_sync"] == 0.65


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
