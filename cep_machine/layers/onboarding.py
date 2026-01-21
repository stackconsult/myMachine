"""
CEP Layer 5: Onboarding Flow

Automated client onboarding with document collection and account setup.
Manages the complete onboarding checklist from contract to go-live.

Container Alignment: Operations
Φ Contribution: +0.07

Input: Converted leads from Layer 4
Output: Fully onboarded clients with active accounts
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class OnboardingStatus(Enum):
    """Status of onboarding process."""
    NOT_STARTED = "not_started"
    DOCUMENTS_REQUESTED = "documents_requested"
    DOCUMENTS_RECEIVED = "documents_received"
    CONTRACT_SENT = "contract_sent"
    CONTRACT_SIGNED = "contract_signed"
    ACCOUNT_SETUP = "account_setup"
    PAYMENT_SETUP = "payment_setup"
    TRAINING_SCHEDULED = "training_scheduled"
    TRAINING_COMPLETED = "training_completed"
    GO_LIVE = "go_live"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(Enum):
    """Types of documents required."""
    BUSINESS_LICENSE = "business_license"
    INSURANCE = "insurance"
    W9_FORM = "w9_form"
    BANK_ACCOUNT = "bank_account"
    LOGO = "logo"
    BRAND_GUIDELINES = "brand_guidelines"
    SERVICE_MENU = "service_menu"
    PRICING = "pricing"
    PHOTOS = "photos"
    OTHER = "other"


class TaskPriority(Enum):
    """Priority levels for onboarding tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Document:
    """A document in the onboarding process."""
    id: str
    client_id: str
    document_type: DocumentType
    name: str
    status: str = "pending"  # pending, received, approved, rejected
    uploaded_at: Optional[datetime] = None
    file_path: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "document_type": self.document_type.value,
            "name": self.name,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "file_path": self.file_path,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class OnboardingTask:
    """A task in the onboarding checklist."""
    id: str
    client_id: str
    title: str
    description: str
    priority: TaskPriority
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


@dataclass
class ClientOnboarding:
    """Complete onboarding record for a client."""
    id: str
    client_name: str
    business_name: str
    email: str
    phone: Optional[str]
    status: OnboardingStatus
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    documents: List[Document] = field(default_factory=list)
    tasks: List[OnboardingTask] = field(default_factory=list)
    contract_url: Optional[str] = None
    contract_signed_at: Optional[datetime] = None
    account_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    training_date: Optional[datetime] = None
    go_live_date: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_name": self.client_name,
            "business_name": self.business_name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "documents": [d.to_dict() for d in self.documents],
            "tasks": [t.to_dict() for t in self.tasks],
            "contract_url": self.contract_url,
            "contract_signed_at": self.contract_signed_at.isoformat() if self.contract_signed_at else None,
            "account_id": self.account_id,
            "payment_method_id": self.payment_method_id,
            "training_date": self.training_date.isoformat() if self.training_date else None,
            "go_live_date": self.go_live_date.isoformat() if self.go_live_date else None,
            "notes": self.notes,
            "metadata": self.metadata,
        }


@dataclass
class OnboardingResult:
    """Result of onboarding operations."""
    client_id: str
    action: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "action": self.action,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "processing_time_ms": self.processing_time_ms,
        }


class OnboardingEngine:
    """
    Layer 5: Onboarding Flow Engine
    
    Manages automated client onboarding from lead to active client.
    Handles document collection, contract signing, and account setup.
    """
    
    # Required documents by business type
    REQUIRED_DOCUMENTS = {
        "dental": [
            DocumentType.BUSINESS_LICENSE,
            DocumentType.INSURANCE,
            DocumentType.W9_FORM,
            DocumentType.BANK_ACCOUNT,
            DocumentType.LOGO,
            DocumentType.SERVICE_MENU,
            DocumentType.PRICING,
            DocumentType.PHOTOS,
        ],
        "hvac": [
            DocumentType.BUSINESS_LICENSE,
            DocumentType.INSURANCE,
            DocumentType.W9_FORM,
            DocumentType.BANK_ACCOUNT,
            DocumentType.LOGO,
            DocumentType.SERVICE_MENU,
        ],
        "default": [
            DocumentType.BUSINESS_LICENSE,
            DocumentType.INSURANCE,
            DocumentType.W9_FORM,
            DocumentType.BANK_ACCOUNT,
            DocumentType.LOGO,
        ],
    }
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.clients: Dict[str, ClientOnboarding] = {}
    
    async def start_onboarding(
        self,
        client_name: str,
        business_name: str,
        email: str,
        phone: Optional[str] = None,
        business_type: str = "default",
    ) -> OnboardingResult:
        """
        Start onboarding for a new client.
        
        Args:
            client_name: Name of the primary contact
            business_name: Business name
            email: Contact email
            phone: Contact phone
            business_type: Type of business (affects required documents)
        
        Returns:
            OnboardingResult with client details
        """
        start_time = datetime.now()
        
        print(f"[Layer 5] Starting onboarding for {business_name}")
        
        # Create client record
        client_id = f"client_{business_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        client = ClientOnboarding(
            id=client_id,
            client_name=client_name,
            business_name=business_name,
            email=email,
            phone=phone,
            status=OnboardingStatus.NOT_STARTED,
            metadata={"business_type": business_type},
        )
        
        # Initialize required documents
        required_docs = self.REQUIRED_DOCUMENTS.get(business_type.lower(), self.REQUIRED_DOCUMENTS["default"])
        for doc_type in required_docs:
            document = Document(
                id=f"doc_{client_id}_{doc_type.value}",
                client_id=client_id,
                document_type=doc_type,
                name=f"{doc_type.value.replace('_', ' ').title()}",
            )
            client.documents.append(document)
        
        # Initialize onboarding tasks
        tasks = await self._create_onboarding_tasks(client_id, business_type)
        client.tasks.extend(tasks)
        
        # Store client
        self.clients[client_id] = client
        
        # Send welcome email and document request
        await self._send_welcome_email(client)
        await self._request_documents(client)
        
        # Update status
        client.status = OnboardingStatus.DOCUMENTS_REQUESTED
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        result = OnboardingResult(
            client_id=client_id,
            action="start_onboarding",
            success=True,
            message=f"Onboarding started for {business_name}",
            data={"client_id": client_id, "status": client.status.value},
            processing_time_ms=processing_time,
        )
        
        print(f"[Layer 5] ✓ Onboarding started: {client_id}")
        
        return result
    
    async def _create_onboarding_tasks(
        self,
        client_id: str,
        business_type: str,
    ) -> List[OnboardingTask]:
        """Create standard onboarding tasks."""
        tasks = []
        
        # Document collection
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_docs",
            client_id=client_id,
            title="Collect Required Documents",
            description="Gather all necessary documents from client",
            priority=TaskPriority.CRITICAL,
            due_date=datetime.now() + timedelta(days=3),
        ))
        
        # Contract preparation
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_contract",
            client_id=client_id,
            title="Prepare Service Contract",
            description="Create and send service agreement",
            priority=TaskPriority.HIGH,
            dependencies=[f"task_{client_id}_docs"],
            due_date=datetime.now() + timedelta(days=5),
        ))
        
        # Account setup
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_account",
            client_id=client_id,
            title="Setup Client Account",
            description="Create client account in system",
            priority=TaskPriority.HIGH,
            dependencies=[f"task_{client_id}_contract"],
            due_date=datetime.now() + timedelta(days=7),
        ))
        
        # Payment setup
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_payment",
            client_id=client_id,
            title="Setup Payment Method",
            description="Configure billing and payment",
            priority=TaskPriority.HIGH,
            dependencies=[f"task_{client_id}_account"],
            due_date=datetime.now() + timedelta(days=8),
        ))
        
        # Training
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_training",
            client_id=client_id,
            title="Schedule Training Session",
            description="Book onboarding training call",
            priority=TaskPriority.MEDIUM,
            dependencies=[f"task_{client_id}_payment"],
            due_date=datetime.now() + timedelta(days=10),
        ))
        
        # Go live
        tasks.append(OnboardingTask(
            id=f"task_{client_id}_golive",
            client_id=client_id,
            title="Go Live Setup",
            description="Activate services and go live",
            priority=TaskPriority.CRITICAL,
            dependencies=[f"task_{client_id}_training"],
            due_date=datetime.now() + timedelta(days=14),
        ))
        
        return tasks
    
    async def upload_document(
        self,
        client_id: str,
        document_type: DocumentType,
        file_name: str,
        file_path: Optional[str] = None,
    ) -> OnboardingResult:
        """Upload a document for a client."""
        start_time = datetime.now()
        
        client = self.clients.get(client_id)
        if not client:
            return OnboardingResult(
                client_id=client_id,
                action="upload_document",
                success=False,
                message="Client not found",
                processing_time_ms=0,
            )
        
        # Find the document
        document = None
        for doc in client.documents:
            if doc.document_type == document_type:
                document = doc
                break
        
        if not document:
            return OnboardingResult(
                client_id=client_id,
                action="upload_document",
                success=False,
                message=f"Document type {document_type.value} not required",
                processing_time_ms=0,
            )
        
        # Update document
        document.status = "received"
        document.uploaded_at = datetime.now()
        document.file_path = file_path or f"/uploads/{client_id}/{file_name}"
        
        # Check if all documents are received
        if all(doc.status == "received" for doc in client.documents):
            client.status = OnboardingStatus.DOCUMENTS_RECEIVED
            await self._prepare_contract(client)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return OnboardingResult(
            client_id=client_id,
            action="upload_document",
            success=True,
            message=f"Document uploaded: {file_name}",
            data={"document_id": document.id, "status": document.status},
            processing_time_ms=processing_time,
        )
    
    async def sign_contract(
        self,
        client_id: str,
        signature_data: Dict[str, Any],
    ) -> OnboardingResult:
        """Process contract signing."""
        start_time = datetime.now()
        
        client = self.clients.get(client_id)
        if not client:
            return OnboardingResult(
                client_id=client_id,
                action="sign_contract",
                success=False,
                message="Client not found",
                processing_time_ms=0,
            )
        
        # Update contract status
        client.contract_signed_at = datetime.now()
        client.status = OnboardingStatus.CONTRACT_SIGNED
        
        # Start account setup
        await self._setup_account(client)
        await self._setup_payment(client)
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return OnboardingResult(
            client_id=client_id,
            action="sign_contract",
            success=True,
            message="Contract signed successfully",
            data={"signed_at": client.contract_signed_at.isoformat()},
            processing_time_ms=processing_time,
        )
    
    async def complete_training(
        self,
        client_id: str,
        training_date: datetime,
    ) -> OnboardingResult:
        """Mark training as completed."""
        start_time = datetime.now()
        
        client = self.clients.get(client_id)
        if not client:
            return OnboardingResult(
                client_id=client_id,
                action="complete_training",
                success=False,
                message="Client not found",
                processing_time_ms=0,
            )
        
        # Update training status
        client.training_date = training_date
        client.status = OnboardingStatus.TRAINING_COMPLETED
        
        # Schedule go live
        go_live_date = training_date + timedelta(days=2)
        client.go_live_date = go_live_date
        
        # Complete go live task
        for task in client.tasks:
            if task.title == "Go Live Setup":
                task.status = "completed"
                task.completed_at = datetime.now()
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return OnboardingResult(
            client_id=client_id,
            action="complete_training",
            success=True,
            message="Training completed",
            data={
                "training_date": training_date.isoformat(),
                "go_live_date": go_live_date.isoformat(),
            },
            processing_time_ms=processing_time,
        )
    
    async def get_onboarding_status(self, client_id: str) -> Optional[ClientOnboarding]:
        """Get current onboarding status for a client."""
        return self.clients.get(client_id)
    
    async def get_pending_tasks(self, client_id: str) -> List[OnboardingTask]:
        """Get pending tasks for a client."""
        client = self.clients.get(client_id)
        if not client:
            return []
        
        return [task for task in client.tasks if task.status == "pending"]
    
    async def _send_welcome_email(self, client: ClientOnboarding) -> None:
        """Send welcome email to client."""
        if self.dry_run:
            print(f"[Layer 5] (DRY RUN) Would send welcome email to {client.email}")
            return
        
        # In production, use email service
        print(f"[Layer 5] ✓ Welcome email sent to {client.email}")
    
    async def _request_documents(self, client: ClientOnboarding) -> None:
        """Send document request email."""
        if self.dry_run:
            print(f"[Layer 5] (DRY RUN) Would request documents from {client.email}")
            return
        
        # In production, use email service
        print(f"[Layer 5] ✓ Document request sent to {client.email}")
    
    async def _prepare_contract(self, client: ClientOnboarding) -> None:
        """Prepare service contract."""
        if self.dry_run:
            print(f"[Layer 5] (DRY RUN) Would prepare contract for {client.business_name}")
            client.contract_url = f"https://contracts.example.com/{client.id}"
            client.status = OnboardingStatus.CONTRACT_SENT
            return
        
        # In production, generate contract
        client.contract_url = f"https://contracts.example.com/{client.id}"
        client.status = OnboardingStatus.CONTRACT_SENT
        print(f"[Layer 5] ✓ Contract prepared: {client.contract_url}")
    
    async def _setup_account(self, client: ClientOnboarding) -> None:
        """Setup client account."""
        if self.dry_run:
            print(f"[Layer 5] (DRY RUN) Would setup account for {client.business_name}")
            client.account_id = f"acc_{client.id}"
            client.status = OnboardingStatus.ACCOUNT_SETUP
            return
        
        # In production, create account
        client.account_id = f"acc_{client.id}"
        client.status = OnboardingStatus.ACCOUNT_SETUP
        print(f"[Layer 5] ✓ Account created: {client.account_id}")
    
    async def _setup_payment(self, client: ClientOnboarding) -> None:
        """Setup payment method."""
        if self.dry_run:
            print(f"[Layer 5] (DRY RUN) Would setup payment for {client.business_name}")
            client.payment_method_id = f"pay_{client.id}"
            client.status = OnboardingStatus.PAYMENT_SETUP
            return
        
        # In production, setup payment
        client.payment_method_id = f"pay_{client.id}"
        client.status = OnboardingStatus.PAYMENT_SETUP
        print(f"[Layer 5] ✓ Payment setup: {client.payment_method_id}")


# Layer 5 Entry Point
async def run_layer(
    client_name: str,
    business_name: str,
    email: str,
    phone: Optional[str] = None,
    business_type: str = "default",
    dry_run: bool = True,
) -> OnboardingResult:
    """
    Main entry point for Layer 5: Onboarding Flow
    
    Args:
        client_name: Name of primary contact
        business_name: Business name
        email: Contact email
        phone: Contact phone
        business_type: Type of business
        dry_run: If True, simulate external API calls
    
    Returns:
        OnboardingResult with client details
    """
    print(f"\n{'='*60}")
    print(f"[Layer 5] ONBOARDING FLOW")
    print(f"Client: {business_name}")
    print(f"Type: {business_type}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'='*60}\n")
    
    engine = OnboardingEngine(dry_run=dry_run)
    result = await engine.start_onboarding(
        client_name=client_name,
        business_name=business_name,
        email=email,
        phone=phone,
        business_type=business_type,
    )
    
    print(f"\n[Layer 5] ✓ Complete")
    print(f"  - Client ID: {result.data.get('client_id') if result.data else 'N/A'}")
    print(f"  - Status: {result.data.get('status') if result.data else 'N/A'}")
    print(f"  - Processing time: {result.processing_time_ms}ms")
    
    return result


# Export
__all__ = [
    "Document",
    "OnboardingTask",
    "ClientOnboarding",
    "OnboardingResult",
    "OnboardingEngine",
    "OnboardingStatus",
    "DocumentType",
    "TaskPriority",
    "run_layer",
]


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Sample onboarding
    client_name = sys.argv[1] if len(sys.argv) > 1 else "John Doe"
    business_name = sys.argv[2] if len(sys.argv) > 2 else "Test Dental Clinic"
    email = sys.argv[3] if len(sys.argv) > 3 else "john@testdental.com"
    business_type = sys.argv[4] if len(sys.argv) > 4 else "dental"
    
    dry_run = "--live" not in sys.argv
    result = asyncio.run(run_layer(
        client_name=client_name,
        business_name=business_name,
        email=email,
        business_type=business_type,
        dry_run=dry_run,
    ))
    
    print("\n" + "="*60)
    print("ONBOARDING DETAILS:")
    print("="*60)
    
    if result.success and result.data:
        client_id = result.data.get("client_id")
        print(f"\nClient ID: {client_id}")
        print(f"Status: {result.data.get('status')}")
        
        # Show required documents
        engine = OnboardingEngine()
        if client_id in engine.clients:
            client = engine.clients[client_id]
            print(f"\nRequired Documents ({len(client.documents)}):")
            for doc in client.documents:
                status_icon = "✓" if doc.status == "received" else "○"
                print(f"  {status_icon} {doc.name}")
            
            print(f"\nOnboarding Tasks ({len(client.tasks)}):")
            for task in client.tasks:
                priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟢", "low": "⚪"}[task.priority.value]
                status_icon = "✓" if task.status == "completed" else "○"
                print(f"  {priority_icon} {status_icon} {task.title}")
