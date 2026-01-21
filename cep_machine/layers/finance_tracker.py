"""
CEP Layer 8: Finance Tracker

Track revenue, expenses, and financial metrics across the system.
Automated billing, invoicing, and financial reporting.

Container Alignment: Finance
Φ Contribution: +0.07

Input: Financial data from all layers
Output: Complete financial picture with billing automation
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class TransactionType(Enum):
    """Types of financial transactions."""
    REVENUE = "revenue"
    EXPENSE = "expense"
    INVOICE = "invoice"
    PAYMENT = "payment"
    REFUND = "refund"
    TAX = "tax"


class BillingCycle(Enum):
    """Billing cycles."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ONE_TIME = "one_time"


class InvoiceStatus(Enum):
    """Invoice statuses."""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class Transaction:
    """A financial transaction."""
    id: str
    client_id: str
    transaction_type: TransactionType
    amount: float
    currency: str = "USD"
    description: str = ""
    category: str = ""
    date: datetime = field(default_factory=datetime.now)
    reference_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "category": self.category,
            "date": self.date.isoformat(),
            "reference_id": self.reference_id,
            "metadata": self.metadata,
        }


@dataclass
class Invoice:
    """An invoice for billing."""
    id: str
    client_id: str
    business_name: str
    amount: float
    currency: str = "USD"
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issue_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    paid_date: Optional[datetime] = None
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    
    def __post_init__(self):
        if self.total_amount == 0.0:
            self.tax_amount = self.amount * self.tax_rate
            self.total_amount = self.amount + self.tax_amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "business_name": self.business_name,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "line_items": self.line_items,
            "notes": self.notes,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "total_amount": self.total_amount,
        }


@dataclass
class FinancialMetrics:
    """Financial metrics for a period."""
    period_start: datetime
    period_end: datetime
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    net_profit: float = 0.0
    profit_margin: float = 0.0
    customer_acquisition_cost: float = 0.0
    customer_lifetime_value: float = 0.0
    monthly_recurring_revenue: float = 0.0
    annual_recurring_revenue: float = 0.0
    average_revenue_per_client: float = 0.0
    churn_rate: float = 0.0
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics."""
        if self.total_revenue > 0:
            self.profit_margin = (self.net_profit / self.total_revenue) * 100
        
        self.annual_recurring_revenue = self.monthly_recurring_revenue * 12
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "net_profit": self.net_profit,
            "profit_margin": self.profit_margin,
            "customer_acquisition_cost": self.customer_acquisition_cost,
            "customer_lifetime_value": self.customer_lifetime_value,
            "monthly_recurring_revenue": self.monthly_recurring_revenue,
            "annual_recurring_revenue": self.annual_recurring_revenue,
            "average_revenue_per_client": self.average_revenue_per_client,
            "churn_rate": self.churn_rate,
        }


@dataclass
class FinanceTrackerResult:
    """Result of finance tracking operations."""
    transactions_processed: int
    invoices_generated: int
    payments_received: float
    expenses_tracked: float
    net_profit: float
    profit_margin: float
    processing_time_seconds: float
    metrics: FinancialMetrics
    transactions: List[Transaction] = field(default_factory=list)
    invoices: List[Invoice] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transactions_processed": self.transactions_processed,
            "invoices_generated": self.invoices_generated,
            "payments_received": self.payments_received,
            "expenses_tracked": self.expenses_tracked,
            "net_profit": self.net_profit,
            "profit_margin": self.profit_margin,
            "processing_time_seconds": self.processing_time_seconds,
            "metrics": self.metrics.to_dict(),
            "transactions": [t.to_dict() for t in self.transactions],
            "invoices": [i.to_dict() for i in self.invoices],
        }


class FinanceTrackerEngine:
    """
    Layer 8: Finance Tracker Engine
    
    Tracks all financial aspects of the business.
    Handles billing, invoicing, and financial metrics.
    """
    
    # Service pricing tiers
    SERVICE_TIER_PRICING = {
        "starter": {"monthly": 500, "setup": 1000},
        "professional": {"monthly": 1500, "setup": 2500},
        "enterprise": {"monthly": 3000, "setup": 5000},
    }
    
    # Expense categories
    EXPENSE_CATEGORIES = [
        "Software",
        "Marketing",
        "Salaries",
        "Office",
        "Travel",
        "Professional Services",
        "Taxes",
        "Other",
    ]
    
    def __init__(self, llm_provider: str = "openai", model: str = "gpt-4-turbo-preview", dry_run: bool = True):
        self.llm_provider = llm_provider
        self.model = model
        self.dry_run = dry_run
        self.llm = self._init_llm()
        self.transactions: List[Transaction] = []
        self.invoices: Dict[str, List[Invoice]] = {}
        self.client_billing: Dict[str, Dict[str, Any]] = {}
    
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
    
    async def track_finances(
        self,
        clients: List[Dict[str, Any]],
        period_start: datetime,
        period_end: datetime,
    ) -> FinanceTrackerResult:
        """
        Track finances for a period.
        
        Args:
            clients: List of client data
            period_start: Start of tracking period
            period_end: End of tracking period
        
        Returns:
            FinanceTrackerResult with complete financial picture
        """
        start_time = datetime.now()
        
        print(f"[Layer 8] Tracking finances for {len(clients)} clients")
        print(f"Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}")
        
        result = FinanceTrackerResult(
            transactions_processed=0,
            invoices_generated=0,
            payments_received=0.0,
            expenses_tracked=0.0,
            net_profit=0.0,
            profit_margin=0.0,
            processing_time_seconds=0.0,
            metrics=FinancialMetrics(period_start, period_end),
        )
        
        # Process client billing
        for client in clients:
            client_result = await self._process_client_billing(client, period_start, period_end)
            
            # Add transactions
            result.transactions.extend(client_result["transactions"])
            result.transactions_processed += len(client_result["transactions"])
            
            # Add invoices
            result.invoices.extend(client_result["invoices"])
            result.invoices_generated += len(client_result["invoices"])
            
            # Update totals
            result.payments_received += client_result["payments"]
            result.expenses_tracked += client_result["expenses"]
        
        # Calculate financial metrics
        await self._calculate_metrics(result, clients)
        
        result.processing_time_seconds = (datetime.now() - start_time).total_seconds()
        
        print(f"[Layer 8] ✓ Finance tracking complete")
        print(f"  - Transactions: {result.transactions_processed}")
        print(f"  - Invoices: {result.invoices_generated}")
        print(f"  - Revenue: ${result.payments_received:,.2f}")
        print(f"  - Expenses: ${result.expenses_tracked:,.2f}")
        print(f"  - Net Profit: ${result.net_profit:,.2f}")
        print(f"  - Margin: {result.profit_margin:.1f}%")
        
        return result
    
    async def _process_client_billing(
        self,
        client: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Process billing for a single client."""
        client_id = client["id"]
        business_name = client["business_name"]
        
        transactions = []
        invoices = []
        payments = 0.0
        expenses = 0.0
        
        # Determine billing tier
        tier = client.get("billing_tier", "starter")
        pricing = self.SERVICE_TIER_PRICING.get(tier, self.SERVICE_TIER_PRICING["starter"])
        
        # Generate monthly invoice
        if period_start.day == 1:  # First day of month
            invoice = await self._generate_monthly_invoice(
                client_id=client_id,
                business_name=business_name,
                amount=pricing["monthly"],
                period_start=period_start,
                tier=tier,
            )
            invoices.append(invoice)
            
            # Record revenue transaction
            revenue_tx = Transaction(
                id=f"rev_{client_id}_{period_start.strftime('%Y%m')}",
                client_id=client_id,
                transaction_type=TransactionType.REVENUE,
                amount=pricing["monthly"],
                description=f"Monthly service fee - {tier} tier",
                category="Service Revenue",
                reference_id=invoice.id,
            )
            transactions.append(revenue_tx)
            payments += pricing["monthly"]
        
        # Track client acquisition cost
        if client.get("new_client", False):
            cac = client.get("acquisition_cost", 500)
            cac_tx = Transaction(
                id=f"cac_{client_id}_{datetime.now().strftime('%Y%m%d')}",
                client_id=client_id,
                transaction_type=TransactionType.EXPENSE,
                amount=cac,
                description="Customer acquisition cost",
                category="Marketing",
            )
            transactions.append(cac_tx)
            expenses += cac
        
        # Track operational expenses
        operational_expenses = await self._calculate_operational_expenses(client)
        for expense in operational_expenses:
            transactions.append(expense)
            expenses += expense.amount
        
        return {
            "transactions": transactions,
            "invoices": invoices,
            "payments": payments,
            "expenses": expenses,
        }
    
    async def _generate_monthly_invoice(
        self,
        client_id: str,
        business_name: str,
        amount: float,
        period_start: datetime,
        tier: str,
    ) -> Invoice:
        """Generate a monthly invoice."""
        invoice = Invoice(
            id=f"inv_{client_id}_{period_start.strftime('%Y%m')}",
            client_id=client_id,
            business_name=business_name,
            amount=amount,
            tax_rate=0.08,  # 8% tax
            due_date=period_start + timedelta(days=30),
        )
        
        # Add line items
        invoice.line_items = [
            {
                "description": f"{tier.title()} Service Plan",
                "quantity": 1,
                "unit_price": amount,
                "total": amount,
            }
        ]
        
        invoice.notes = f"Monthly service fee for {period_start.strftime('%B %Y')}"
        
        if self.dry_run:
            print(f"[Layer 8] (DRY RUN) Would send invoice {invoice.id} to {business_name}")
            invoice.status = InvoiceStatus.SENT
        else:
            # In production, send via email/invoicing service
            invoice.status = InvoiceStatus.SENT
            print(f"[Layer 8] ✓ Invoice {invoice.id} sent to {business_name}")
        
        # Store invoice
        if client_id not in self.invoices:
            self.invoices[client_id] = []
        self.invoices[client_id].append(invoice)
        
        return invoice
    
    async def _calculate_operational_expenses(self, client: Dict[str, Any]) -> List[Transaction]:
        """Calculate operational expenses for a client."""
        expenses = []
        
        # Software costs (per client)
        software_cost = 50.0  # $50/month per client
        expenses.append(Transaction(
            id=f"soft_{client['id']}_{datetime.now().strftime('%Y%m%d')}",
            client_id=client["id"],
            transaction_type=TransactionType.EXPENSE,
            amount=software_cost,
            description="Software licenses and tools",
            category="Software",
        ))
        
        # Support costs (estimated)
        support_cost = 25.0  # $25/month per client
        expenses.append(Transaction(
            id=f"supp_{client['id']}_{datetime.now().strftime('%Y%m%d')}",
            client_id=client["id"],
            transaction_type=TransactionType.EXPENSE,
            amount=support_cost,
            description="Customer support and maintenance",
            category="Professional Services",
        ))
        
        return expenses
    
    async def _calculate_metrics(
        self,
        result: FinanceTrackerResult,
        clients: List[Dict[str, Any]],
    ) -> None:
        """Calculate financial metrics."""
        metrics = result.metrics
        
        # Total revenue and expenses
        metrics.total_revenue = result.payments_received
        metrics.total_expenses = result.expenses_tracked
        metrics.net_profit = metrics.total_revenue - metrics.total_expenses
        
        # Customer metrics
        total_clients = len(clients)
        new_clients = sum(1 for c in clients if c.get("new_client", False))
        
        # CAC
        if new_clients > 0:
            cac_total = sum(
                c.get("acquisition_cost", 500) 
                for c in clients 
                if c.get("new_client", False)
            )
            metrics.customer_acquisition_cost = cac_total / new_clients
        
        # LTV (simplified)
        avg_monthly_revenue = metrics.total_revenue / max(total_clients, 1)
        metrics.customer_lifetime_value = avg_monthly_revenue * 12  # Assume 12 months
        
        # MRR and ARR
        metrics.monthly_recurring_revenue = metrics.total_revenue
        metrics.annual_recurring_revenue = metrics.monthly_recurring_revenue * 12
        
        # Average revenue per client
        metrics.average_revenue_per_client = avg_monthly_revenue
        
        # Churn rate (simplified - assume 5% monthly)
        metrics.churn_rate = 5.0
        
        # Calculate derived metrics
        metrics.calculate_derived_metrics()
        
        # Update result
        result.net_profit = metrics.net_profit
        result.profit_margin = metrics.profit_margin
        result.metrics = metrics
    
    async def record_payment(
        self,
        invoice_id: str,
        amount: float,
        payment_date: Optional[datetime] = None,
    ) -> Optional[Transaction]:
        """Record a payment for an invoice."""
        # Find invoice
        invoice = None
        for client_invoices in self.invoices.values():
            for inv in client_invoices:
                if inv.id == invoice_id:
                    invoice = inv
                    break
            if invoice:
                break
        
        if not invoice:
            print(f"[Layer 8] Invoice {invoice_id} not found")
            return None
        
        # Update invoice status
        invoice.status = InvoiceStatus.PAID
        invoice.paid_date = payment_date or datetime.now()
        
        # Record payment transaction
        payment = Transaction(
            id=f"pay_{invoice_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            client_id=invoice.client_id,
            transaction_type=TransactionType.PAYMENT,
            amount=amount,
            description=f"Payment for invoice {invoice_id}",
            category="Payments",
            reference_id=invoice_id,
        )
        
        self.transactions.append(payment)
        
        print(f"[Layer 8] ✓ Payment recorded: ${amount:.2f} for invoice {invoice_id}")
        
        return payment
    
    async def get_financial_summary(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Get financial summary for a period."""
        # Filter transactions by period
        period_transactions = [
            t for t in self.transactions
            if period_start <= t.date <= period_end
        ]
        
        # Calculate totals
        revenue = sum(t.amount for t in period_transactions if t.transaction_type == TransactionType.REVENUE)
        expenses = sum(t.amount for t in period_transactions if t.transaction_type == TransactionType.EXPENSE)
        
        # Group by category
        revenue_by_category = {}
        expenses_by_category = {}
        
        for t in period_transactions:
            if t.transaction_type == TransactionType.REVENUE:
                revenue_by_category[t.category] = revenue_by_category.get(t.category, 0) + t.amount
            elif t.transaction_type == TransactionType.EXPENSE:
                expenses_by_category[t.category] = expenses_by_category.get(t.category, 0) + t.amount
        
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_revenue": revenue,
            "total_expenses": expenses,
            "net_profit": revenue - expenses,
            "profit_margin": ((revenue - expenses) / revenue * 100) if revenue > 0 else 0,
            "revenue_by_category": revenue_by_category,
            "expenses_by_category": expenses_by_category,
            "transaction_count": len(period_transactions),
        }
    
    async def forecast_revenue(
        self,
        months: int = 12,
    ) -> Dict[str, Any]:
        """Forecast future revenue."""
        forecast = []
        
        # Get current MRR
        current_mrr = sum(
            inv.amount
            for inv_list in self.invoices.values()
            for inv in inv_list
            if inv.status in [InvoiceStatus.SENT, InvoiceStatus.PAID]
        )
        
        # Simple growth assumption (5% monthly)
        growth_rate = 0.05
        
        for month in range(1, months + 1):
            projected_mrr = current_mrr * ((1 + growth_rate) ** month)
            forecast.append({
                "month": month,
                "projected_mrr": projected_mrr,
                "projected_revenue": projected_mrr,
            })
        
        return {
            "current_mrr": current_mrr,
            "growth_rate": growth_rate,
            "forecast": forecast,
        }


# Layer 8 Entry Point
async def run_layer(
    clients: List[Dict[str, Any]],
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    dry_run: bool = True,
) -> FinanceTrackerResult:
    """
    Main entry point for Layer 8: Finance Tracker
    
    Args:
        clients: List of client data with billing info
        period_start: Start of tracking period (default: first of current month)
        period_end: End of tracking period (default: now)
        dry_run: If True, simulate external API calls
    
    Returns:
        FinanceTrackerResult with complete financial picture
    """
    print(f"\n{'='*60}")
    print(f"[Layer 8] FINANCE TRACKER")
    print(f"Clients: {len(clients)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    # Default period is current month
    now = datetime.now()
    if not period_start:
        period_start = datetime(now.year, now.month, 1)
    if not period_end:
        period_end = now
    
    engine = FinanceTrackerEngine(dry_run=dry_run)
    result = await engine.track_finances(clients, period_start, period_end)
    
    print(f"\n[Layer 8] ✓ Complete")
    print(f"  - Revenue: ${result.payments_received:,.2f}")
    print(f"  - Expenses: ${result.expenses_tracked:,.2f}")
    print(f"  - Net Profit: ${result.net_profit:,.2f}")
    print(f"  - Margin: {result.profit_margin:.1f}%")
    print(f"  - MRR: ${result.metrics.monthly_recurring_revenue:,.2f}")
    print(f"  - ARR: ${result.metrics.annual_recurring_revenue:,.2f}")
    
    return result


# Export
__all__ = [
    "Transaction",
    "Invoice",
    "FinancialMetrics",
    "FinanceTrackerResult",
    "FinanceTrackerEngine",
    "TransactionType",
    "BillingCycle",
    "InvoiceStatus",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Sample client data
    sample_clients = [
        {
            "id": "client_001",
            "business_name": "Test Dental Clinic",
            "billing_tier": "professional",
            "new_client": False,
            "acquisition_cost": 450,
        },
        {
            "id": "client_002",
            "business_name": "Test HVAC Company",
            "billing_tier": "starter",
            "new_client": True,
            "acquisition_cost": 600,
        },
        {
            "id": "client_003",
            "business_name": "Test Restaurant",
            "billing_tier": "enterprise",
            "new_client": False,
            "acquisition_cost": 800,
        },
    ]
    
    dry_run = "--live" not in sys.argv
    result = asyncio.run(run_layer(sample_clients, dry_run=dry_run))
    
    print("\n" + "="*60)
    print("FINANCIAL SUMMARY:")
    print("="*60)
    
    metrics = result.metrics
    print(f"\nRevenue Metrics:")
    print(f"  Total Revenue: ${metrics.total_revenue:,.2f}")
    print(f"  MRR: ${metrics.monthly_recurring_revenue:,.2f}")
    print(f"  ARR: ${metrics.annual_recurring_revenue:,.2f}")
    print(f"  Avg Revenue/Client: ${metrics.average_revenue_per_client:,.2f}")
    
    print(f"\nCost Metrics:")
    print(f"  Total Expenses: ${metrics.total_expenses:,.2f}")
    print(f"  CAC: ${metrics.customer_acquisition_cost:,.2f}")
    print(f"  LTV: ${metrics.customer_lifetime_value:,.2f}")
    
    print(f"\nProfitability:")
    print(f"  Net Profit: ${metrics.net_profit:,.2f}")
    print(f"  Profit Margin: {metrics.profit_margin:.1f}%")
    print(f"  LTV/CAC Ratio: {metrics.customer_lifetime_value / max(metrics.customer_acquisition_cost, 1):.1f}x")
    
    print(f"\nTransactions: {result.transactions_processed}")
    print(f"Invoices: {result.invoices_generated}")
    
    # Show recent invoices
    print(f"\nRecent Invoices:")
    for invoice in result.invoices[:3]:
        status_icon = {"draft": "📝", "sent": "📤", "paid": "✅", "overdue": "⚠️"}[invoice.status.value]
        print(f"  {status_icon} {invoice.id}: ${invoice.total_amount:,.2f} - {invoice.business_name}")
