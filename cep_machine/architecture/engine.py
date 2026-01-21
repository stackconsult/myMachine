"""
CEP Architecture Engine - Replaces Claude Code ($200/mo)

Workflow: Parse Request → Retrieve Research → Generate Specs → Validate against CEP Rules

Uses LangGraph for orchestration with Claude API for reasoning.
Cost: ~$5-10/month (pay-as-you-go API calls)
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass, field
from enum import Enum

from langgraph.graph import StateGraph, END

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..core.database import Database


class ArchitecturePhase(Enum):
    UNDERSTAND = "understand"
    DESIGN = "design"
    VALIDATE = "validate"
    DOCUMENT = "document"


@dataclass
class LayerArchitecture:
    """Architecture specification for a layer."""
    layer_id: int
    layer_name: str
    description: str
    inputs: List[Dict[str, str]]
    outputs: List[Dict[str, str]]
    dependencies: List[int]
    functions: List[Dict[str, Any]]
    database_tables: List[str]
    cep_validation: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "functions": self.functions,
            "database_tables": self.database_tables,
            "cep_validation": self.cep_validation,
            "created_at": self.created_at.isoformat(),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class ArchitectureState(TypedDict):
    """State for the architecture LangGraph workflow."""
    layer_id: int
    layer_name: str
    requirements: str
    research_context: str
    understanding: str
    design: Dict[str, Any]
    validation_result: Dict[str, Any]
    final_architecture: Optional[LayerArchitecture]
    errors: List[str]


class ArchitectureEngine:
    """
    Architecture Engine - Designs system architectures using LangGraph.
    
    Replaces Claude Code with:
    - LangGraph for workflow orchestration
    - Claude/OpenAI API for reasoning (pay-per-use)
    - CEP validation rules
    """
    
    def __init__(
        self,
        db: Optional[Database] = None,
        llm_provider: str = "openai",
        model: str = "gpt-4-turbo-preview",
    ):
        self.db = db or Database()
        self.llm_provider = llm_provider
        self.model = model
        self.llm = self._init_llm()
        self.workflow = self._build_workflow()
    
    def _init_llm(self):
        """Initialize the LLM based on provider."""
        if self.llm_provider == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return ChatAnthropic(
                    model=self.model or "claude-3-sonnet-20240229",
                    anthropic_api_key=api_key,
                )
        
        if self.llm_provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return ChatOpenAI(
                    model=self.model or "gpt-4-turbo-preview",
                    openai_api_key=api_key,
                )
        
        return None
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for architecture design."""
        workflow = StateGraph(ArchitectureState)
        
        # Add nodes
        workflow.add_node("understand", self._understand_node)
        workflow.add_node("design", self._design_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("document", self._document_node)
        
        # Add edges
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "design")
        workflow.add_edge("design", "validate")
        workflow.add_edge("validate", "document")
        workflow.add_edge("document", END)
        
        return workflow.compile()
    
    async def _understand_node(self, state: ArchitectureState) -> ArchitectureState:
        """Understand the requirements."""
        print(f"[Architecture] Understanding Layer {state['layer_id']}: {state['layer_name']}")
        
        if not self.llm:
            state["understanding"] = f"Layer {state['layer_id']}: {state['requirements']}"
            return state
        
        prompt = f"""Analyze these requirements for Layer {state['layer_id']} ({state['layer_name']}):

Requirements: {state['requirements']}

Research Context: {state['research_context'][:1000] if state['research_context'] else 'None provided'}

Provide a clear understanding of:
1. Core purpose
2. Key inputs needed
3. Expected outputs
4. Integration points with other layers

Keep response concise (150 words max)."""
        
        try:
            response = await self.llm.ainvoke(prompt)
            state["understanding"] = response.content
        except Exception as e:
            state["understanding"] = f"Requirements: {state['requirements']}"
            state["errors"].append(f"Understanding error: {str(e)}")
        
        return state
    
    async def _design_node(self, state: ArchitectureState) -> ArchitectureState:
        """Design the architecture."""
        print(f"[Architecture] Designing Layer {state['layer_id']}...")
        
        if not self.llm:
            state["design"] = self._create_default_design(state)
            return state
        
        prompt = f"""Design the architecture for Layer {state['layer_id']} ({state['layer_name']}).

Understanding:
{state['understanding']}

Return a JSON architecture with:
{{
    "inputs": [{{"name": "input_name", "type": "string", "description": "..."}}],
    "outputs": [{{"name": "output_name", "type": "string", "description": "..."}}],
    "dependencies": [1, 2],  // layer IDs this depends on
    "functions": [
        {{"name": "function_name", "purpose": "...", "params": ["param1"], "returns": "..."}}
    ],
    "database_tables": ["table1", "table2"]
}}

Return ONLY valid JSON."""
        
        try:
            response = await self.llm.ainvoke(prompt)
            # Parse JSON from response
            content = response.content
            # Try to extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            state["design"] = json.loads(content.strip())
        except Exception as e:
            state["design"] = self._create_default_design(state)
            state["errors"].append(f"Design error: {str(e)}")
        
        return state
    
    def _create_default_design(self, state: ArchitectureState) -> Dict[str, Any]:
        """Create a default design when LLM is unavailable."""
        return {
            "inputs": [{"name": "input_data", "type": "dict", "description": "Input data"}],
            "outputs": [{"name": "result", "type": "dict", "description": "Processing result"}],
            "dependencies": [],
            "functions": [
                {
                    "name": f"process_layer_{state['layer_id']}",
                    "purpose": state["requirements"][:100],
                    "params": ["input_data"],
                    "returns": "result",
                }
            ],
            "database_tables": [f"layer_{state['layer_id']}_data"],
        }
    
    async def _validate_node(self, state: ArchitectureState) -> ArchitectureState:
        """Validate against CEP rules."""
        print(f"[Architecture] Validating Layer {state['layer_id']}...")
        
        validation = {
            "valid": True,
            "phi_contribution": 0.0,
            "warnings": [],
            "container_alignment": "unknown",
        }
        
        design = state["design"]
        
        # Rule 1: Must have inputs and outputs
        if not design.get("inputs"):
            validation["warnings"].append("No inputs defined")
        if not design.get("outputs"):
            validation["warnings"].append("No outputs defined")
        
        # Rule 2: Must have at least one function
        if not design.get("functions"):
            validation["warnings"].append("No functions defined")
            validation["valid"] = False
        
        # Rule 3: Calculate phi contribution based on layer
        layer_id = state["layer_id"]
        if layer_id <= 3:
            validation["phi_contribution"] = 0.07
            validation["container_alignment"] = "Sales"
        elif layer_id <= 6:
            validation["phi_contribution"] = 0.06
            validation["container_alignment"] = "Operations"
        else:
            validation["phi_contribution"] = 0.05
            validation["container_alignment"] = "Finance"
        
        state["validation_result"] = validation
        return state
    
    async def _document_node(self, state: ArchitectureState) -> ArchitectureState:
        """Create final architecture document."""
        print(f"[Architecture] Documenting Layer {state['layer_id']}...")
        
        design = state["design"]
        validation = state["validation_result"]
        
        architecture = LayerArchitecture(
            layer_id=state["layer_id"],
            layer_name=state["layer_name"],
            description=state["requirements"],
            inputs=design.get("inputs", []),
            outputs=design.get("outputs", []),
            dependencies=design.get("dependencies", []),
            functions=design.get("functions", []),
            database_tables=design.get("database_tables", []),
            cep_validation=validation,
        )
        
        state["final_architecture"] = architecture
        
        # Save to database
        if self.db:
            try:
                await self.db.save_architecture(
                    layer_id=state["layer_id"],
                    architecture_json=architecture.to_json(),
                    validated=validation.get("valid", False),
                )
            except Exception as e:
                state["errors"].append(f"Database save error: {str(e)}")
        
        return state
    
    async def design_layer(
        self,
        layer_id: int,
        layer_name: str,
        requirements: str,
        research_context: str = "",
    ) -> LayerArchitecture:
        """
        Design architecture for a layer.
        
        Args:
            layer_id: Layer number (1-9)
            layer_name: Name of the layer
            requirements: What the layer should do
            research_context: Optional research findings
        
        Returns:
            LayerArchitecture with complete specification
        """
        initial_state: ArchitectureState = {
            "layer_id": layer_id,
            "layer_name": layer_name,
            "requirements": requirements,
            "research_context": research_context,
            "understanding": "",
            "design": {},
            "validation_result": {},
            "final_architecture": None,
            "errors": [],
        }
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        if final_state.get("errors"):
            print(f"[Architecture] Warnings: {final_state['errors']}")
        
        architecture = final_state.get("final_architecture")
        if architecture:
            print(f"[Architecture] ✓ Layer {layer_id} architecture complete")
            print(f"  - Φ contribution: {architecture.cep_validation.get('phi_contribution', 0):.2f}")
            print(f"  - Container: {architecture.cep_validation.get('container_alignment')}")
        
        return architecture
