"""
Finance Tracker Agent - Layer 8
CrewAI-based financial operations and tracking
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import json
import uuid

# CrewAI imports
from crewai import Flow, Task, Agent
from crewai.flow import start, listen

# CopilotKit imports
from copilotkit.langchain import copilotkit_emit_state

# CEP Machine imports
from cep_machine.layers.finance_tracker import FinanceTracker
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class FinanceFlow(Flow):
    """CrewAI Flow for financial operations"""
    
    def __init__(self):
        super().__init__()
        self.finance_tracker = FinanceTracker()
        self.db = get_database()
        self.cache = get_cache()
        self.flow_id = str(uuid.uuid4())
    
    @start()
    async def detect_transactions(self):
        """Start transaction detection and categorization"""
        # Get recent transactions from bank feeds
        transactions = await self._fetch_bank_transactions(days=7)
        
        # Categorize transactions
        categorized = []
        for transaction in transactions:
            category = await self._categorize_transaction(transaction)
            categorized.append({
                **transaction,
                "category": category,
                "processed_at": datetime.now().isoformat()
            })
        
        # Update ledger
        await self._update_ledger(categorized)
        
        # Emit transaction updates
        await copilotkit_emit_state(
            {
                "type": "transactions_processed",
                "data": {
                    "count": len(categorized),
                    "total_amount": sum(t["amount"] for t in categorized)
                }
            },
            {"channel": "finance_updates"}
        )
        
        # Update state
        self.state.update({
            "transactions": categorized,
            "stage": "invoice_generation"
        })
        
        return {"status": "transactions_detected", "count": len(categorized)}
    
    @listen("detect_transactions")
    async def generate_invoices(self):
        """Generate monthly invoices for clients"""
        # Get active clients
        clients = await self.db.list("clients", filters={"status": "active"})
        
        invoices = []
        for client in clients:
            # Calculate billing amount
            billing_amount = await self._calculate_client_billing(client)
            
            # Generate invoice
            invoice = {
                "id": f"inv_{datetime.now().timestamp()}_{client['id']}",
                "client_id": client["id"],
                "amount": billing_amount,
                "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "status": "draft",
                "line_items": await self._generate_invoice_items(client),
                "created_at": datetime.now().isoformat()
            }
            
            # Store invoice
            await self.db.create("invoices", invoice)
            invoices.append(invoice)
        
        # Send invoices to clients
        for invoice in invoices:
            await self._send_invoice(invoice)
        
        # Emit invoice generation update
        await copilotkit_emit_state(
            {
                "type": "invoices_generated",
                "data": {
                    "count": len(invoices),
                    "total_amount": sum(inv["amount"] for inv in invoices)
                }
            },
            {"channel": "finance_updates"}
        )
        
        # Update state
        self.state.update({
            "invoices": invoices,
            "stage": "payment_processing"
        })
        
        return {"status": "invoices_generated", "invoices": invoices}
    
    @listen("generate_invoices")
    async def process_payments(self):
        """Process incoming payments and update records"""
        # Get unpaid invoices
        unpaid_invoices = await self.db.list(
            "invoices",
            filters={"status": "sent"}
        )
        
        payments_processed = []
        
        for invoice in unpaid_invoices:
            # Check for payments
            payment = await self._check_payment_status(invoice)
            
            if payment:
                # Record payment
                payment_record = {
                    "id": f"pay_{datetime.now().timestamp()}",
                    "invoice_id": invoice["id"],
                    "amount": payment["amount"],
                    "payment_method": payment["method"],
                    "paid_at": payment["date"],
                    "status": "completed"
                }
                
                await self.db.create("payments", payment_record)
                
                # Update invoice status
                await self.db.update(
                    "invoices",
                    invoice["id"],
                    {"status": "paid", "paid_at": payment["date"]}
                )
                
                # Update client status
                await self._update_client_payment_status(invoice["client_id"])
                
                payments_processed.append(payment_record)
        
        # Handle late payments
        late_payments = await self._process_late_payments(unpaid_invoices)
        
        # Emit payment updates
        await copilotkit_emit_state(
            {
                "type": "payments_processed",
                "data": {
                    "payments": len(payments_processed),
                    "late_payments": len(late_payments),
                    "total_amount": sum(p["amount"] for p in payments_processed)
                }
            },
            {"channel": "finance_updates"}
        )
        
        # Update state
        self.state.update({
            "payments": payments_processed,
            "late_payments": late_payments,
            "stage": "calculate_metrics"
        })
        
        return {
            "status": "payments_processed",
            "payments": payments_processed,
            "late_payments": late_payments
        }
    
    @listen("process_payments")
    async def calculate_metrics(self):
        """Calculate financial metrics and KPIs"""
        # Get financial data
        transactions = self.state.get("transactions", [])
        invoices = self.state.get("invoices", [])
        payments = self.state.get("payments", [])
        
        # Calculate metrics
        metrics = {
            "revenue": {
                "total": sum(p["amount"] for p in payments),
                "recurring": await self._calculate_recurring_revenue(),
                "new": await self._calculate_new_revenue()
            },
            "expenses": {
                "total": sum(t["amount"] for t in transactions if t["amount"] < 0),
                "by_category": await self._group_expenses_by_category(transactions)
            },
            "profitability": {
                "gross_profit": 0,  # Will calculate
                "net_profit": 0,    # Will calculate
                "profit_margin": 0   # Will calculate
            },
            "cash_flow": {
                "inflow": sum(p["amount"] for p in payments),
                "outflow": abs(sum(t["amount"] for t in transactions if t["amount"] < 0)),
                "net": 0  # Will calculate
            },
            "accounts_receivable": {
                "total": sum(inv["amount"] for inv in invoices if inv["status"] == "sent"),
                "overdue": await self._calculate_overdue_amount(invoices)
            }
        }
        
        # Calculate derived metrics
        metrics["profitability"]["gross_profit"] = metrics["revenue"]["total"] + metrics["expenses"]["total"]
        metrics["profitability"]["net_profit"] = metrics["profitability"]["gross_profit"]
        metrics["profitability"]["profit_margin"] = (
            metrics["profitability"]["net_profit"] / metrics["revenue"]["total"]
            if metrics["revenue"]["total"] > 0 else 0
        )
        metrics["cash_flow"]["net"] = metrics["cash_flow"]["inflow"] - metrics["cash_flow"]["outflow"]
        
        # Store metrics
        await self.db.create("financial_metrics", {
            "id": self.flow_id,
            "metrics": metrics,
            "calculated_at": datetime.now().isoformat()
        })
        
        # Update state
        self.state.update({
            "metrics": metrics,
            "stage": "generate_forecasts"
        })
        
        return {"status": "metrics_calculated", "metrics": metrics}
    
    @listen("calculate_metrics")
    async def generate_forecasts(self):
        """Generate financial forecasts and projections"""
        metrics = self.state["metrics"]
        
        # Get historical data
        historical_metrics = await self._get_historical_metrics(months=12)
        
        # Generate revenue forecast
        revenue_forecast = await self._forecast_revenue(
            current_revenue=metrics["revenue"]["total"],
            historical_data=historical_metrics
        )
        
        # Generate expense forecast
        expense_forecast = await self._forecast_expenses(
            current_expenses=metrics["expenses"]["total"],
            historical_data=historical_metrics
        )
        
        # Generate cash flow forecast
        cash_flow_forecast = await self._forecast_cash_flow(
            metrics["cash_flow"],
            historical_data=historical_metrics
        )
        
        # Generate profit forecast
        profit_forecast = await self._forecast_profit(
            revenue_forecast,
            expense_forecast
        )
        
        forecasts = {
            "revenue": revenue_forecast,
            "expenses": expense_forecast,
            "cash_flow": cash_flow_forecast,
            "profit": profit_forecast,
            "generated_at": datetime.now().isoformat(),
            "forecast_period": "6_months"
        }
        
        # Store forecasts
        await self.db.create("financial_forecasts", {
            "id": self.flow_id,
            "forecasts": forecasts,
            "created_at": datetime.now().isoformat()
        })
        
        # Generate insights
        insights = await self._generate_financial_insights(metrics, forecasts)
        
        # Emit forecast updates
        await copilotkit_emit_state(
            {
                "type": "forecasts_generated",
                "data": {
                    "forecasts": forecasts,
                    "insights": insights
                }
            },
            {"channel": "finance_updates"}
        )
        
        return {
            "status": "forecasts_generated",
            "forecasts": forecasts,
            "insights": insights
        }
    
    # Helper methods
    async def _fetch_bank_transactions(self, days: int = 7) -> List[Dict]:
        """Fetch transactions from bank feeds"""
        # Mock implementation - integrate with bank API
        return [
            {"id": "1", "amount": 5000, "description": "Client payment", "date": "2024-01-21"},
            {"id": "2", "amount": -200, "description": "Software subscription", "date": "2024-01-20"},
            {"id": "3", "amount": -1500, "description": "Office rent", "date": "2024-01-19"}
        ]
    
    async def _categorize_transaction(self, transaction: Dict) -> str:
        """Categorize transaction based on description"""
        description = transaction["description"].lower()
        
        if "client" in description or "payment" in description:
            return "revenue"
        elif "rent" in description:
            return "rent"
        elif "software" in description or "subscription" in description:
            return "software"
        elif "salary" in description or "payroll" in description:
            return "payroll"
        else:
            return "other"
    
    async def _update_ledger(self, transactions: List[Dict]):
        """Update financial ledger with transactions"""
        for transaction in transactions:
            await self.db.create("ledger", transaction)
    
    async def _calculate_client_billing(self, client: Dict) -> float:
        """Calculate billing amount for client"""
        # Mock calculation based on client plan
        base_rate = client.get("monthly_rate", 1000)
        usage_multiplier = client.get("usage_multiplier", 1.0)
        return base_rate * usage_multiplier
    
    async def _generate_invoice_items(self, client: Dict) -> List[Dict]:
        """Generate line items for invoice"""
        return [
            {"description": "Monthly subscription", "quantity": 1, "unit_price": client.get("monthly_rate", 1000)},
            {"description": "Additional services", "quantity": client.get("additional_hours", 0), "unit_price": 150}
        ]
    
    async def _send_invoice(self, invoice: Dict):
        """Send invoice to client"""
        # Update invoice status
        await self.db.update(
            "invoices",
            invoice["id"],
            {"status": "sent", "sent_at": datetime.now().isoformat()}
        )
        
        # Log communication
        await self.db.create("communications", {
            "client_id": invoice["client_id"],
            "type": "invoice_sent",
            "invoice_id": invoice["id"],
            "sent_at": datetime.now().isoformat()
        })
    
    async def _check_payment_status(self, invoice: Dict) -> Optional[Dict]:
        """Check if invoice has been paid"""
        # Mock implementation - check payment gateway
        # In production, integrate with Stripe, PayPal, etc.
        
        # Simulate some invoices being paid
        if hash(invoice["id"]) % 3 == 0:  # Every 3rd invoice is "paid"
            return {
                "amount": invoice["amount"],
                "method": "bank_transfer",
                "date": datetime.now().isoformat()
            }
        
        return None
    
    async def _update_client_payment_status(self, client_id: str):
        """Update client payment status"""
        await self.db.update(
            "clients",
            client_id,
            {"last_payment": datetime.now().isoformat()}
        )
    
    async def _process_late_payments(self, invoices: List[Dict]) -> List[Dict]:
        """Process and flag late payments"""
        late_payments = []
        today = datetime.now()
        
        for invoice in invoices:
            due_date = datetime.fromisoformat(invoice["due_date"])
            if today > due_date and invoice["status"] == "sent":
                late_payments.append({
                    "invoice_id": invoice["id"],
                    "client_id": invoice["client_id"],
                    "days_late": (today - due_date).days,
                    "amount": invoice["amount"]
                })
                
                # Update invoice status
                await self.db.update(
                    "invoices",
                    invoice["id"],
                    {"status": "overdue", "days_overdue": (today - due_date).days}
                )
        
        return late_payments
    
    async def _calculate_recurring_revenue(self) -> float:
        """Calculate monthly recurring revenue (MRR)"""
        # Mock calculation
        return 75000
    
    async def _calculate_new_revenue(self) -> float:
        """Calculate new revenue this period"""
        # Mock calculation
        return 25000
    
    async def _group_expenses_by_category(self, transactions: List[Dict]) -> Dict:
        """Group expenses by category"""
        expenses = [t for t in transactions if t["amount"] < 0]
        grouped = {}
        
        for expense in expenses:
            category = expense.get("category", "other")
            if category not in grouped:
                grouped[category] = 0
            grouped[category] += abs(expense["amount"])
        
        return grouped
    
    async def _calculate_overdue_amount(self, invoices: List[Dict]) -> float:
        """Calculate total overdue amount"""
        today = datetime.now()
        overdue_total = 0
        
        for invoice in invoices:
            if invoice["status"] == "sent":
                due_date = datetime.fromisoformat(invoice["due_date"])
                if today > due_date:
                    overdue_total += invoice["amount"]
        
        return overdue_total
    
    async def _get_historical_metrics(self, months: int = 12) -> List[Dict]:
        """Get historical financial metrics"""
        # Mock implementation
        return [
            {"month": "2023-12", "revenue": 100000, "expenses": 60000},
            {"month": "2024-01", "revenue": 125000, "expenses": 75000}
        ]
    
    async def _forecast_revenue(self, current_revenue: float, historical_data: List[Dict]) -> Dict:
        """Forecast revenue based on historical trends"""
        # Simple linear regression forecast
        if len(historical_data) < 2:
            growth_rate = 0.1  # Default 10% growth
        else:
            # Calculate growth rate from historical data
            recent = historical_data[-1]["revenue"]
            previous = historical_data[-2]["revenue"]
            growth_rate = (recent - previous) / previous if previous > 0 else 0.1
        
        forecast = []
        projected_revenue = current_revenue
        
        for month in range(1, 7):  # 6 month forecast
            projected_revenue *= (1 + growth_rate)
            forecast.append({
                "month": month,
                "projected_revenue": projected_revenue
            })
        
        return {
            "current": current_revenue,
            "growth_rate": growth_rate,
            "forecast": forecast
        }
    
    async def _forecast_expenses(self, current_expenses: float, historical_data: List[Dict]) -> Dict:
        """Forecast expenses based on historical trends"""
        # Similar to revenue forecast but with lower growth
        growth_rate = 0.05  # 5% expense growth
        
        forecast = []
        projected_expenses = current_expenses
        
        for month in range(1, 7):
            projected_expenses *= (1 + growth_rate)
            forecast.append({
                "month": month,
                "projected_expenses": projected_expenses
            })
        
        return {
            "current": current_expenses,
            "growth_rate": growth_rate,
            "forecast": forecast
        }
    
    async def _forecast_cash_flow(self, current_cash_flow: Dict, historical_data: List[Dict]) -> Dict:
        """Forecast cash flow"""
        # Simple cash flow projection
        forecast = []
        
        for month in range(1, 7):
            # Mock seasonal variations
            seasonal_factor = 1.0 + (0.1 * (month % 3 - 1))
            projected_inflow = current_cash_flow["inflow"] * seasonal_factor
            projected_outflow = current_cash_flow["outflow"] * 1.02  # 2% increase
            
            forecast.append({
                "month": month,
                "projected_inflow": projected_inflow,
                "projected_outflow": projected_outflow,
                "projected_net": projected_inflow - projected_outflow
            })
        
        return {
            "current": current_cash_flow,
            "forecast": forecast
        }
    
    async def _forecast_profit(self, revenue_forecast: Dict, expense_forecast: Dict) -> Dict:
        """Forecast profit based on revenue and expense forecasts"""
        forecast = []
        
        for month in range(6):
            revenue = revenue_forecast["forecast"][month]["projected_revenue"]
            expenses = expense_forecast["forecast"][month]["projected_expenses"]
            
            forecast.append({
                "month": month + 1,
                "projected_revenue": revenue,
                "projected_expenses": expenses,
                "projected_profit": revenue - expenses,
                "profit_margin": (revenue - expenses) / revenue if revenue > 0 else 0
            })
        
        return {
            "forecast": forecast
        }
    
    async def _generate_financial_insights(self, metrics: Dict, forecasts: Dict) -> List[Dict]:
        """Generate insights from financial data"""
        insights = []
        
        # Revenue insights
        if metrics["revenue"]["recurring"] / metrics["revenue"]["total"] > 0.8:
            insights.append({
                "type": "positive",
                "title": "Strong Recurring Revenue",
                "description": "80% of revenue is recurring, indicating stable business model"
            })
        
        # Cash flow insights
        if metrics["cash_flow"]["net"] < 0:
            insights.append({
                "type": "warning",
                "title": "Negative Cash Flow",
                "description": "Current cash flow is negative, review expenses and collections"
            })
        
        # Forecast insights
        avg_profit_margin = sum(f["profit_margin"] for f in forecasts["profit"]["forecast"]) / 6
        if avg_profit_margin > 0.2:
            insights.append({
                "type": "positive",
                "title": "Strong Profit Forecast",
                "description": f"Projected profit margin of {avg_profit_margin * 100:.1f}% over next 6 months"
            })
        
        return insights

# Create the finance tracker agent
def create_finance_tracker_agent():
    """Create and configure the finance tracker agent"""
    
    agent = Agent(
        role="Finance Manager",
        goal="Track and optimize all financial operations",
        backstory="""You are a seasoned finance manager who ensures
        accurate financial tracking, timely invoicing, and provides
        valuable insights for business growth.""",
        tools=[
            "detect_transactions",
            "generate_invoices",
            "process_payments",
            "calculate_metrics",
            "generate_forecasts"
        ],
        verbose=True
    )
    
    return agent

# Export the flow and agent
__all__ = ["FinanceFlow", "create_finance_tracker_agent"]
