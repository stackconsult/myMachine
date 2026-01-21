"""
Onboarding Flow Agent - Layer 5
CrewAI-based multi-stage onboarding process automation
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
from cep_machine.layers.onboarding import Onboarding
from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

class OnboardingFlow(Flow):
    """CrewAI Flow for client onboarding process"""
    
    def __init__(self):
        super().__init__()
        self.onboarding = Onboarding()
        self.db = get_database()
        self.cache = get_cache()
        self.flow_id = str(uuid.uuid4())
    
    @start()
    async def initiate_onboarding(self):
        """Start the onboarding process for a new client"""
        # Get client details from trigger
        client_id = self.state.get("client_id")
        
        if not client_id:
            raise ValueError("Client ID required to start onboarding")
        
        # Create onboarding record
        onboarding_record = {
            "id": self.flow_id,
            "client_id": client_id,
            "status": "initiated",
            "current_stage": "data_collection",
            "started_at": datetime.now().isoformat(),
            "progress": {
                "data_collection": 0,
                "service_setup": 0,
                "document_generation": 0,
                "kickoff_meeting": 0
            }
        }
        
        await self.db.create("onboarding_flows", onboarding_record)
        
        # Send welcome email
        await self._send_welcome_email(client_id)
        
        # Emit state update
        await copilotkit_emit_state(
            {
                "type": "onboarding_started",
                "data": {
                    "flow_id": self.flow_id,
                    "client_id": client_id,
                    "stage": "data_collection"
                }
            },
            {"channel": f"onboarding_{client_id}"}
        )
        
        # Update state for next stage
        self.state.update({
            "client_id": client_id,
            "onboarding_id": self.flow_id,
            "stage": "data_collection"
        })
        
        return {"status": "onboarding_initiated", "flow_id": self.flow_id}
    
    @listen("initiate_onboarding")
    async def collect_business_data(self):
        """Stage 1: Collect business information and requirements"""
        client_id = self.state["client_id"]
        onboarding_id = self.state["onboarding_id"]
        
        # Create data collection task
        data_collection = {
            "client_id": client_id,
            "tasks": [
                "business_information",
                "service_requirements",
                "team_contacts",
                "technical_preferences"
            ],
            "status": "in_progress",
            "due_date": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        await self.db.create("onboarding_tasks", data_collection)
        
        # Generate data collection forms
        forms = await self.onboarding.generate_data_forms(client_id)
        
        # Send data collection request
        await self._send_data_request(client_id, forms)
        
        # Update progress
        await self._update_progress(onboarding_id, "data_collection", 50)
        
        # Wait for data completion (in production, this would be async)
        # For now, simulate completion
        await asyncio.sleep(2)
        
        collected_data = await self._collect_submitted_data(client_id)
        
        # Update state
        self.state.update({
            "collected_data": collected_data,
            "stage": "service_setup"
        })
        
        return {"status": "data_collected", "data": collected_data}
    
    @listen("collect_business_data")
    async def setup_services(self):
        """Stage 2: Provision and configure client services"""
        client_id = self.state["client_id"]
        onboarding_id = self.state["onboarding_id"]
        collected_data = self.state["collected_data"]
        
        # Create parallel service setup tasks
        service_tasks = [
            self._provision_accounts(client_id, collected_data),
            self._configure_tools(client_id, collected_data),
            self._set_permissions(client_id, collected_data),
            self._initialize_integrations(client_id, collected_data)
        ]
        
        # Execute tasks in parallel
        service_setup_results = await asyncio.gather(*service_tasks)
        
        # Consolidate results
        setup_summary = {
            "accounts_created": service_setup_results[0],
            "tools_configured": service_setup_results[1],
            "permissions_set": service_setup_results[2],
            "integrations_active": service_setup_results[3]
        }
        
        # Update progress
        await self._update_progress(onboarding_id, "service_setup", 100)
        
        # Send setup confirmation
        await self._send_setup_confirmation(client_id, setup_summary)
        
        # Update state
        self.state.update({
            "service_setup": setup_summary,
            "stage": "document_generation"
        })
        
        return {"status": "services_setup", "summary": setup_summary}
    
    @listen("setup_services")
    async def generate_documents(self):
        """Stage 3: Generate onboarding documents"""
        client_id = self.state["client_id"]
        onboarding_id = self.state["onboarding_id"]
        collected_data = self.state["collected_data"]
        service_setup = self.state["service_setup"]
        
        # Generate document package
        documents = await asyncio.gather(
            self._generate_welcome_packet(client_id, collected_data),
            self._generate_service_agreement(client_id, collected_data),
            self._generate_training_materials(client_id, service_setup),
            self._generate_quick_start_guide(client_id)
        )
        
        document_package = {
            "welcome_packet": documents[0],
            "service_agreement": documents[1],
            "training_materials": documents[2],
            "quick_start_guide": documents[3],
            "generated_at": datetime.now().isoformat()
        }
        
        # Store documents
        await self.db.create("onboarding_documents", {
            "client_id": client_id,
            "documents": document_package
        })
        
        # Update progress
        await self._update_progress(onboarding_id, "document_generation", 100)
        
        # Send documents to client
        await self._send_documents(client_id, document_package)
        
        # Update state
        self.state.update({
            "documents": document_package,
            "stage": "kickoff_meeting"
        })
        
        return {"status": "documents_generated", "package": document_package}
    
    @listen("generate_documents")
    async def schedule_kickoff(self):
        """Stage 4: Schedule and prepare kickoff meeting"""
        client_id = self.state["client_id"]
        onboarding_id = self.state["onboarding_id"]
        
        # Generate kickoff agenda
        agenda = await self._generate_kickoff_agenda(client_id)
        
        # Schedule meeting (integrate with booking handler)
        meeting_details = {
            "client_id": client_id,
            "meeting_type": "kickoff",
            "duration": 60,
            "agenda": agenda,
            "preferred_times": [
                {"start": datetime.now() + timedelta(days=2), "duration": 60},
                {"start": datetime.now() + timedelta(days=3), "duration": 60},
                {"start": datetime.now() + timedelta(days=4), "duration": 60}
            ]
        }
        
        # Create kickoff meeting request
        kickoff_request = await self.db.create("kickoff_requests", meeting_details)
        
        # Update progress
        await self._update_progress(onboarding_id, "kickoff_meeting", 50)
        
        # Send meeting invitation
        await self._send_kickoff_invitation(client_id, kickoff_request)
        
        # Complete onboarding flow
        await self._complete_onboarding(onboarding_id)
        
        # Emit completion state
        await copilotkit_emit_state(
            {
                "type": "onboarding_completed",
                "data": {
                    "flow_id": onboarding_id,
                    "client_id": client_id,
                    "kickoff_scheduled": True
                }
            },
            {"channel": f"onboarding_{client_id}"}
        )
        
        return {
            "status": "onboarding_completed",
            "kickoff_request": kickoff_request,
            "flow_id": onboarding_id
        }
    
    # Helper methods
    async def _send_welcome_email(self, client_id: str):
        """Send welcome email to new client"""
        welcome = {
            "client_id": client_id,
            "template": "welcome",
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("communications", welcome)
    
    async def _send_data_request(self, client_id: str, forms: Dict):
        """Send data collection request"""
        request = {
            "client_id": client_id,
            "type": "data_collection",
            "forms": forms,
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("communications", request)
    
    async def _collect_submitted_data(self, client_id: str) -> Dict:
        """Collect and validate submitted data"""
        # Mock implementation - in production, fetch from forms
        return {
            "business_name": "Sample Business",
            "industry": "Technology",
            "team_size": 50,
            "requirements": ["automation", "reporting"]
        }
    
    async def _provision_accounts(self, client_id: str, data: Dict) -> List[str]:
        """Provision user accounts"""
        # Mock implementation
        return ["main_account", "analytics_account", "reporting_account"]
    
    async def _configure_tools(self, client_id: str, data: Dict) -> List[str]:
        """Configure client tools"""
        # Mock implementation
        return ["crm_configured", "analytics_setup", "dashboard_ready"]
    
    async def _set_permissions(self, client_id: str, data: Dict) -> List[str]:
        """Set user permissions"""
        # Mock implementation
        return ["admin_access", "user_roles_set", "api_keys_generated"]
    
    async def _initialize_integrations(self, client_id: str, data: Dict) -> List[str]:
        """Initialize third-party integrations"""
        # Mock implementation
        return ["slack_connected", "email_synced", "calendar_linked"]
    
    async def _send_setup_confirmation(self, client_id: str, summary: Dict):
        """Send service setup confirmation"""
        confirmation = {
            "client_id": client_id,
            "type": "setup_confirmation",
            "summary": summary,
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("communications", confirmation)
    
    async def _generate_welcome_packet(self, client_id: str, data: Dict) -> Dict:
        """Generate welcome packet"""
        return {
            "title": "Welcome to CEP Machine",
            "sections": ["getting_started", "support", "best_practices"],
            "document_url": f"/docs/welcome_{client_id}.pdf"
        }
    
    async def _generate_service_agreement(self, client_id: str, data: Dict) -> Dict:
        """Generate service agreement"""
        return {
            "title": "Service Agreement",
            "terms": "service_terms",
            "document_url": f"/docs/agreement_{client_id}.pdf"
        }
    
    async def _generate_training_materials(self, client_id: str, setup: Dict) -> Dict:
        """Generate training materials"""
        return {
            "videos": ["intro_video", "features_tour"],
            "guides": ["user_guide", "admin_guide"],
            "document_url": f"/docs/training_{client_id}.pdf"
        }
    
    async def _generate_quick_start_guide(self, client_id: str) -> Dict:
        """Generate quick start guide"""
        return {
            "steps": ["step1", "step2", "step3"],
            "estimated_time": "30 minutes",
            "document_url": f"/docs/quickstart_{client_id}.pdf"
        }
    
    async def _send_documents(self, client_id: str, package: Dict):
        """Send document package to client"""
        delivery = {
            "client_id": client_id,
            "type": "document_delivery",
            "package": package,
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("communications", delivery)
    
    async def _generate_kickoff_agenda(self, client_id: str) -> List[Dict]:
        """Generate kickoff meeting agenda"""
        return [
            {"title": "Introductions", "duration": 10},
            {"title": "Goals Review", "duration": 15},
            {"title": "System Demo", "duration": 20},
            {"title": "Next Steps", "duration": 15}
        ]
    
    async def _send_kickoff_invitation(self, client_id: str, request: Dict):
        """Send kickoff meeting invitation"""
        invitation = {
            "client_id": client_id,
            "type": "meeting_invitation",
            "meeting_request": request,
            "sent_at": datetime.now().isoformat()
        }
        await self.db.create("communications", invitation)
    
    async def _update_progress(self, onboarding_id: str, stage: str, progress: int):
        """Update onboarding progress"""
        await self.db.update(
            "onboarding_flows",
            onboarding_id,
            {
                f"progress.{stage}": progress,
                "updated_at": datetime.now().isoformat()
            }
        )
    
    async def _complete_onboarding(self, onboarding_id: str):
        """Mark onboarding as completed"""
        await self.db.update(
            "onboarding_flows",
            onboarding_id,
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "progress.kickoff_meeting": 100
            }
        )

# Create the onboarding agent
def create_onboarding_agent():
    """Create and configure the onboarding agent"""
    
    agent = Agent(
        role="Onboarding Specialist",
        goal="Seamlessly onboard new clients through automated workflows",
        backstory="""You are an expert client onboarding specialist who ensures
        every new client has a smooth, professional onboarding experience.
        You coordinate multiple processes and keep clients informed at every step.""",
        tools=[
            "initiate_onboarding",
            "collect_business_data",
            "setup_services",
            "generate_documents",
            "schedule_kickoff"
        ],
        verbose=True
    )
    
    return agent

# Export the flow and agent
__all__ = ["OnboardingFlow", "create_onboarding_agent"]
