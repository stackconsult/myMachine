"""
Tests for Layer 8: Finance Tracker

Success Criteria: 3 test clients tracked with complete financial metrics.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.finance_tracker import (
    Transaction,
    Invoice,
    FinancialMetrics,
    FinanceTrackerResult,
    FinanceTrackerEngine,
    TransactionType,
    BillingCycle,
    InvoiceStatus,
    run_layer,
)


class TestTransaction:
    """Test Transaction data class."""
    
    def test_transaction_creation(self):
        """Test creating a transaction."""
        tx = Transaction(
            id="tx_001",
            client_id="client_001",
            transaction_type=TransactionType.REVENUE,
            amount=1000.0,
            description="Monthly service fee",
        )
        
        assert tx.id == "tx_001"
        assert tx.transaction_type == TransactionType.REVENUE
        assert tx.amount == 1000.0
        assert tx.currency == "USD"
    
    def test_transaction_to_dict(self):
        """Test transaction serialization."""
        tx = Transaction(
            id="tx_001",
            client_id="client_001",
            transaction_type=TransactionType.REVENUE,
            amount=1000.0,
            date=datetime.now(),
        )
        
        data = tx.to_dict()
        assert data["id"] == "tx_001"
        assert data["transaction_type"] == "revenue"
        assert data["amount"] == 1000.0
        assert data["date"] is not None


class TestInvoice:
    """Test Invoice data class."""
    
    def test_invoice_creation(self):
        """Test creating an invoice."""
        invoice = Invoice(
            id="inv_001",
            client_id="client_001",
            business_name="Test Business",
            amount=1000.0,
            tax_rate=0.08,
        )
        
        assert invoice.id == "inv_001"
        assert invoice.amount == 1000.0
        assert invoice.tax_amount == 80.0
        assert invoice.total_amount == 1080.0
        assert invoice.status == InvoiceStatus.DRAFT
    
    def test_invoice_status_update(self):
        """Test updating invoice status."""
        invoice = Invoice(
            id="inv_001",
            client_id="client_001",
            business_name="Test Business",
            amount=1000.0,
        )
        
        invoice.status = InvoiceStatus.PAID
        invoice.paid_date = datetime.now()
        
        assert invoice.status == InvoiceStatus.PAID
        assert invoice.paid_date is not None
    
    def test_invoice_to_dict(self):
        """Test invoice serialization."""
        invoice = Invoice(
            id="inv_001",
            client_id="client_001",
            business_name="Test Business",
            amount=1000.0,
            tax_rate=0.08,
            status=InvoiceStatus.SENT,
        )
        
        data = invoice.to_dict()
        assert data["id"] == "inv_001"
        assert data["status"] == "sent"
        assert data["total_amount"] == 1080.0


class TestFinancialMetrics:
    """Test FinancialMetrics data class."""
    
    def test_metrics_creation(self):
        """Test creating financial metrics."""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        
        metrics = FinancialMetrics(
            period_start=start,
            period_end=end,
            total_revenue=10000.0,
            total_expenses=6000.0,
        )
        
        assert metrics.period_start == start
        assert metrics.period_end == end
        assert metrics.total_revenue == 10000.0
        assert metrics.total_expenses == 6000.0
    
    def test_calculate_derived_metrics(self):
        """Test calculating derived metrics."""
        metrics = FinancialMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_revenue=10000.0,
            total_expenses=6000.0,
            monthly_recurring_revenue=10000.0,
        )
        
        metrics.calculate_derived_metrics()
        
        assert metrics.net_profit == 4000.0
        assert metrics.profit_margin == 40.0
        assert metrics.annual_recurring_revenue == 120000.0
    
    def test_metrics_to_dict(self):
        """Test metrics serialization."""
        metrics = FinancialMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_revenue=10000.0,
        )
        
        data = metrics.to_dict()
        assert data["total_revenue"] == 10000.0
        assert data["period_start"] is not None
        assert data["period_end"] is not None


class TestFinanceTrackerEngine:
    """Test FinanceTrackerEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return FinanceTrackerEngine(dry_run=True)
    
    @pytest.fixture
    def sample_clients(self):
        return [
            {
                "id": "client_001",
                "business_name": "Test Dental",
                "billing_tier": "professional",
                "new_client": False,
                "acquisition_cost": 450,
            },
            {
                "id": "client_002",
                "business_name": "Test HVAC",
                "billing_tier": "starter",
                "new_client": True,
                "acquisition_cost": 600,
            },
        ]
    
    @pytest.mark.asyncio
    async def test_track_finances(self, engine, sample_clients):
        """Test tracking finances for clients."""
        period_start = datetime.now().replace(day=1)
        period_end = datetime.now()
        
        result = await engine.track_finances(
            clients=sample_clients,
            period_start=period_start,
            period_end=period_end,
        )
        
        assert isinstance(result, FinanceTrackerResult)
        assert result.transactions_processed > 0
        assert result.invoices_generated > 0
        assert result.payments_received > 0
        assert result.expenses_tracked > 0
        assert result.net_profit >= 0
        assert len(result.transactions) > 0
        assert len(result.invoices) > 0
    
    @pytest.mark.asyncio
    async def test_process_client_billing(self, engine):
        """Test processing billing for a client."""
        client = {
            "id": "client_001",
            "business_name": "Test Business",
            "billing_tier": "professional",
            "new_client": True,
            "acquisition_cost": 500,
        }
        
        period_start = datetime.now().replace(day=1)
        period_end = datetime.now()
        
        result = await engine._process_client_billing(client, period_start, period_end)
        
        assert "transactions" in result
        assert "invoices" in result
        assert "payments" in result
        assert "expenses" in result
        
        assert len(result["invoices"]) > 0
        assert result["payments"] > 0
        assert result["expenses"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_monthly_invoice(self, engine):
        """Test generating a monthly invoice."""
        invoice = await engine._generate_monthly_invoice(
            client_id="client_001",
            business_name="Test Business",
            amount=1500.0,
            period_start=datetime.now().replace(day=1),
            tier="professional",
        )
        
        assert invoice.client_id == "client_001"
        assert invoice.amount == 1500.0
        assert invoice.tax_rate == 0.08
        assert invoice.total_amount == 1620.0
        assert invoice.status == InvoiceStatus.SENT
        assert len(invoice.line_items) > 0
    
    @pytest.mark.asyncio
    async def test_calculate_operational_expenses(self, engine):
        """Test calculating operational expenses."""
        client = {"id": "client_001"}
        
        expenses = await engine._calculate_operational_expenses(client)
        
        assert len(expenses) > 0
        assert all(exp.transaction_type == TransactionType.EXPENSE for exp in expenses)
        
        # Check specific expense categories
        categories = [exp.category for exp in expenses]
        assert "Software" in categories
        assert "Professional Services" in categories
    
    @pytest.mark.asyncio
    async def test_calculate_metrics(self, engine, sample_clients):
        """Test calculating financial metrics."""
        result = FinanceTrackerResult(
            transactions_processed=10,
            invoices_generated=5,
            payments_received=5000.0,
            expenses_tracked=2000.0,
            processing_time_seconds=1.0,
            metrics=FinancialMetrics(
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
            ),
        )
        
        await engine._calculate_metrics(result, sample_clients)
        
        assert result.metrics.total_revenue == 5000.0
        assert result.metrics.total_expenses == 2000.0
        assert result.metrics.net_profit == 3000.0
        assert result.metrics.profit_margin == 60.0
        assert result.metrics.monthly_recurring_revenue == 5000.0
        assert result.metrics.annual_recurring_revenue == 60000.0
    
    @pytest.mark.asyncio
    async def test_record_payment(self, engine):
        """Test recording a payment."""
        # First create an invoice
        invoice = Invoice(
            id="inv_001",
            client_id="client_001",
            business_name="Test Business",
            amount=1000.0,
            status=InvoiceStatus.SENT,
        )
        engine.invoices["client_001"] = [invoice]
        
        # Record payment
        payment = await engine.record_payment(
            invoice_id="inv_001",
            amount=1080.0,  # Including tax
        )
        
        assert payment is not None
        assert payment.transaction_type == TransactionType.PAYMENT
        assert payment.amount == 1080.0
        assert payment.reference_id == "inv_001"
        
        # Check invoice status updated
        assert invoice.status == InvoiceStatus.PAID
        assert invoice.paid_date is not None
    
    @pytest.mark.asyncio
    async def test_get_financial_summary(self, engine):
        """Test getting financial summary."""
        # Add some transactions
        engine.transactions = [
            Transaction(
                id="tx_001",
                client_id="client_001",
                transaction_type=TransactionType.REVENUE,
                amount=1000.0,
                category="Service Revenue",
                date=datetime.now(),
            ),
            Transaction(
                id="tx_002",
                client_id="client_001",
                transaction_type=TransactionType.EXPENSE,
                amount=300.0,
                category="Software",
                date=datetime.now(),
            ),
        ]
        
        summary = await engine.get_financial_summary(
            period_start=datetime.now() - timedelta(days=1),
            period_end=datetime.now(),
        )
        
        assert summary["total_revenue"] == 1000.0
        assert summary["total_expenses"] == 300.0
        assert summary["net_profit"] == 700.0
        assert summary["profit_margin"] == 70.0
        assert "Service Revenue" in summary["revenue_by_category"]
        assert "Software" in summary["expenses_by_category"]
    
    @pytest.mark.asyncio
    async def test_forecast_revenue(self, engine):
        """Test revenue forecasting."""
        # Add some invoices for MRR calculation
        engine.invoices = {
            "client_001": [
                Invoice(
                    id="inv_001",
                    client_id="client_001",
                    business_name="Test Business",
                    amount=1000.0,
                    status=InvoiceStatus.PAID,
                )
            ]
        }
        
        forecast = await engine.forecast_revenue(months=12)
        
        assert "current_mrr" in forecast
        assert "growth_rate" in forecast
        assert "forecast" in forecast
        assert len(forecast["forecast"]) == 12
        
        # Check forecast growth
        assert forecast["forecast"][0]["projected_mrr"] > forecast["current_mrr"]
        assert forecast["forecast"][-1]["projected_mrr"] > forecast["forecast"][0]["projected_mrr"]


class TestLayerEntry:
    """Test Layer 8 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        clients = [
            {
                "id": "client_001",
                "business_name": "Test Business",
                "billing_tier": "professional",
                "new_client": False,
            }
        ]
        
        result = await run_layer(clients, dry_run=True)
        
        assert isinstance(result, FinanceTrackerResult)
        assert result.transactions_processed > 0
        assert result.invoices_generated > 0
        assert result.payments_received > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
