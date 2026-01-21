"""
Tests for Layer 5: Onboarding Flow

Success Criteria: 3 test clients onboarded with automated checklist.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from cep_machine.layers.onboarding import (
    Document,
    OnboardingTask,
    ClientOnboarding,
    OnboardingResult,
    OnboardingEngine,
    OnboardingStatus,
    DocumentType,
    TaskPriority,
    run_layer,
)


class TestDocument:
    """Test Document data class."""
    
    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            id="doc_001",
            client_id="client_001",
            document_type=DocumentType.BUSINESS_LICENSE,
            name="Business License",
        )
        
        assert doc.id == "doc_001"
        assert doc.document_type == DocumentType.BUSINESS_LICENSE
        assert doc.status == "pending"
    
    def test_document_to_dict(self):
        """Test document serialization."""
        doc = Document(
            id="doc_001",
            client_id="client_001",
            document_type=DocumentType.BUSINESS_LICENSE,
            name="Business License",
            uploaded_at=datetime.now(),
        )
        
        data = doc.to_dict()
        assert data["id"] == "doc_001"
        assert data["document_type"] == "business_license"
        assert data["status"] == "pending"
        assert data["uploaded_at"] is not None


class TestOnboardingTask:
    """Test OnboardingTask data class."""
    
    def test_task_creation(self):
        """Test creating an onboarding task."""
        task = OnboardingTask(
            id="task_001",
            client_id="client_001",
            title="Test Task",
            description="Test description",
            priority=TaskPriority.HIGH,
        )
        
        assert task.id == "task_001"
        assert task.priority == TaskPriority.HIGH
        assert task.status == "pending"
    
    def test_task_dependencies(self):
        """Test task dependencies."""
        task = OnboardingTask(
            id="task_002",
            client_id="client_001",
            title="Dependent Task",
            description="Depends on task 001",
            priority=TaskPriority.MEDIUM,
            dependencies=["task_001"],
        )
        
        assert len(task.dependencies) == 1
        assert "task_001" in task.dependencies


class TestClientOnboarding:
    """Test ClientOnboarding data class."""
    
    def test_client_creation(self):
        """Test creating a client onboarding record."""
        client = ClientOnboarding(
            id="client_001",
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
            status=OnboardingStatus.NOT_STARTED,
        )
        
        assert client.id == "client_001"
        assert client.business_name == "Test Business"
        assert client.status == OnboardingStatus.NOT_STARTED
    
    def test_client_to_dict(self):
        """Test client serialization."""
        client = ClientOnboarding(
            id="client_001",
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
            status=OnboardingStatus.DOCUMENTS_REQUESTED,
        )
        
        data = client.to_dict()
        assert data["id"] == "client_001"
        assert data["business_name"] == "Test Business"
        assert data["status"] == "documents_requested"


class TestOnboardingEngine:
    """Test OnboardingEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        return OnboardingEngine(dry_run=True)
    
    @pytest.mark.asyncio
    async def test_start_onboarding(self, engine):
        """Test starting onboarding for a client."""
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Dental",
            email="john@test.com",
            business_type="dental",
        )
        
        assert result.success
        assert result.action == "start_onboarding"
        assert result.data is not None
        assert "client_id" in result.data
        
        # Check client was created
        client_id = result.data["client_id"]
        client = engine.clients.get(client_id)
        assert client is not None
        assert client.business_name == "Test Dental"
        assert client.status == OnboardingStatus.DOCUMENTS_REQUESTED
    
    @pytest.mark.asyncio
    async def test_required_documents_by_type(self, engine):
        """Test required documents vary by business type."""
        # Dental business
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Dental",
            email="john@test.com",
            business_type="dental",
        )
        
        client_id = result.data["client_id"]
        client = engine.clients[client_id]
        
        # Should have dental-specific documents
        doc_types = [doc.document_type for doc in client.documents]
        assert DocumentType.SERVICE_MENU in doc_types
        assert DocumentType.PRICING in doc_types
        assert DocumentType.PHOTOS in doc_types
        
        # HVAC business
        result2 = await engine.start_onboarding(
            client_name="Jane Doe",
            business_name="Test HVAC",
            email="jane@test.com",
            business_type="hvac",
        )
        
        client_id2 = result2.data["client_id"]
        client2 = engine.clients[client_id2]
        
        # Should have fewer documents
        doc_types2 = [doc.document_type for doc in client2.documents]
        assert DocumentType.SERVICE_MENU in doc_types2
        assert DocumentType.PRICING not in doc_types2
        assert DocumentType.PHOTOS not in doc_types2
    
    @pytest.mark.asyncio
    async def test_upload_document(self, engine):
        """Test uploading a document."""
        # Start onboarding first
        start_result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
        )
        
        client_id = start_result.data["client_id"]
        
        # Upload a document
        upload_result = await engine.upload_document(
            client_id=client_id,
            document_type=DocumentType.BUSINESS_LICENSE,
            file_name="license.pdf",
        )
        
        assert upload_result.success
        assert upload_result.action == "upload_document"
        
        # Check document was updated
        client = engine.clients[client_id]
        doc = next(d for d in client.documents if d.document_type == DocumentType.BUSINESS_LICENSE)
        assert doc.status == "received"
        assert doc.uploaded_at is not None
    
    @pytest.mark.asyncio
    async def test_all_documents_received_triggers_contract(self, engine):
        """Test that receiving all documents triggers contract preparation."""
        # Start onboarding
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
            business_type="default",  # Fewer documents for easier testing
        )
        
        client_id = result.data["client_id"]
        client = engine.clients[client_id]
        
        # Upload all required documents
        for doc in client.documents:
            await engine.upload_document(
                client_id=client_id,
                document_type=doc.document_type,
                file_name=f"{doc.document_type.value}.pdf",
            )
        
        # Check status changed
        client = engine.clients[client_id]
        assert client.status == OnboardingStatus.DOCUMENTS_RECEIVED
        assert client.contract_url is not None
    
    @pytest.mark.asyncio
    async def test_sign_contract(self, engine):
        """Test contract signing process."""
        # Start onboarding and complete documents
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
        )
        
        client_id = result.data["client_id"]
        
        # Simulate contract signing
        sign_result = await engine.sign_contract(
            client_id=client_id,
            signature_data={"signature": "dummy_signature"},
        )
        
        assert sign_result.success
        assert sign_result.action == "sign_contract"
        
        # Check account was created
        client = engine.clients[client_id]
        assert client.contract_signed_at is not None
        assert client.account_id is not None
        assert client.payment_method_id is not None
        assert client.status == OnboardingStatus.PAYMENT_SETUP
    
    @pytest.mark.asyncio
    async def test_complete_training(self, engine):
        """Test training completion."""
        # Start onboarding and sign contract
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
        )
        
        client_id = result.data["client_id"]
        
        # Complete training
        training_date = datetime.now() + timedelta(days=1)
        training_result = await engine.complete_training(
            client_id=client_id,
            training_date=training_date,
        )
        
        assert training_result.success
        assert training_result.action == "complete_training"
        
        # Check training and go live dates
        client = engine.clients[client_id]
        assert client.training_date == training_date
        assert client.go_live_date is not None
        assert client.status == OnboardingStatus.TRAINING_COMPLETED
    
    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, engine):
        """Test getting pending tasks."""
        result = await engine.start_onboarding(
            client_name="John Doe",
            business_name="Test Business",
            email="john@test.com",
        )
        
        client_id = result.data["client_id"]
        pending_tasks = await engine.get_pending_tasks(client_id)
        
        # Should have all tasks pending initially
        assert len(pending_tasks) > 0
        assert all(task.status == "pending" for task in pending_tasks)


class TestLayerEntry:
    """Test Layer 5 entry point."""
    
    @pytest.mark.asyncio
    async def test_run_layer(self):
        """Test the main run_layer function."""
        result = await run_layer(
            client_name="Test Client",
            business_name="Test Business",
            email="test@example.com",
            business_type="dental",
            dry_run=True,
        )
        
        assert isinstance(result, OnboardingResult)
        assert result.success
        assert result.action == "start_onboarding"
        assert result.data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
