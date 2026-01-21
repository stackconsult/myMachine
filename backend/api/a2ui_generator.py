"""
A2UI Generator API
Generates A2UI specifications from natural language descriptions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from pathlib import Path

# Add parent directory to path for CEP modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/api/a2ui", tags=["a2ui"])

class A2UIGenerationRequest(BaseModel):
    description: str
    context: Optional[Dict[str, Any]] = None
    style: Optional[str] = "modern"
    complexity: Optional[str] = "medium"  # simple, medium, complex

class A2UIComponent(BaseModel):
    type: str
    props: Optional[Dict[str, Any]] = {}
    children: Optional[List["A2UIComponent"]] = []

class A2UISpec(BaseModel):
    version: str = "1.0"
    components: List[A2UIComponent]
    metadata: Optional[Dict[str, Any]] = {}

# Component templates for A2UI
COMPONENT_TEMPLATES = {
    "button": {
        "type": "button",
        "props": {
            "label": "Click me",
            "variant": "primary",
            "size": "medium"
        }
    },
    "text": {
        "type": "text",
        "props": {
            "content": "Hello, World!",
            "style": "body"
        }
    },
    "input": {
        "type": "input",
        "props": {
            "placeholder": "Enter text...",
            "type": "text"
        }
    },
    "card": {
        "type": "card",
        "props": {
            "title": "Card Title",
            "elevation": "medium"
        },
        "children": []
    },
    "container": {
        "type": "container",
        "props": {
            "direction": "column",
            "spacing": "medium"
        },
        "children": []
    },
    "form": {
        "type": "form",
        "props": {
            "title": "Form",
            "submitLabel": "Submit"
        },
        "children": []
    },
    "chart": {
        "type": "chart",
        "props": {
            "chartType": "line",
            "data": [],
            "xAxis": "x",
            "yAxis": "y"
        }
    },
    "table": {
        "type": "table",
        "props": {
            "columns": [],
            "rows": [],
            "sortable": True
        }
    },
    "list": {
        "type": "list",
        "props": {
            "items": [],
            "variant": "unordered"
        }
    },
    "image": {
        "type": "image",
        "props": {
            "src": "",
            "alt": "Image",
            "width": "auto",
            "height": "auto"
        }
    }
}

@router.post("/generate")
async def generate_a2ui(request: A2UIGenerationRequest):
    """Generate A2UI specification from description"""
    try:
        # Use OpenAI to generate A2UI spec
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create prompt for A2UI generation
        prompt = f"""
Generate an A2UI specification for the following UI description:

Description: {request.description}
Style: {request.style}
Complexity: {request.complexity}

Context: {request.context or {}}

Available component types:
{', '.join(COMPONENT_TEMPLATES.keys())}

Generate a valid JSON response with the following structure:
{{
    "version": "1.0",
    "components": [
        {{
            "type": "container",
            "props": {{
                "direction": "column",
                "spacing": "medium"
            }},
            "children": [
                // Nested components here
            ]
        }}
    ],
    "metadata": {{
        "title": "Generated UI",
        "description": "UI generated from description"
    }}
}}

Ensure the JSON is valid and the component structure makes sense.
"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert UI designer who generates A2UI specifications. Always return valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse the response
        import json
        import re
        
        content = response.choices[0].message.content
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            spec_json = json_match.group()
            spec = json.loads(spec_json)
            
            # Validate and enhance the spec
            spec = validate_and_enhance_spec(spec)
            
            return {
                "spec": spec,
                "raw_response": content
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate valid A2UI spec")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def validate_and_enhance_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enhance the generated A2UI spec"""
    # Ensure version
    if "version" not in spec:
        spec["version"] = "1.0"
    
    # Validate components
    if "components" not in spec:
        spec["components"] = []
    
    # Recursively validate components
    def validate_component(component: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure type is valid
        if component["type"] not in COMPONENT_TEMPLATES:
            # Default to container if invalid type
            component["type"] = "container"
        
        # Ensure props exist
        if "props" not in component:
            component["props"] = {}
        
        # Merge with template props
        template = COMPONENT_TEMPLATES[component["type"]]
        for key, value in template.get("props", {}).items():
            if key not in component["props"]:
                component["props"][key] = value
        
        # Validate children
        if "children" in component and component["children"]:
            component["children"] = [
                validate_component(child) for child in component["children"]
            ]
        
        return component
    
    # Validate all components
    spec["components"] = [
        validate_component(comp) for comp in spec["components"]
    ]
    
    # Ensure metadata
    if "metadata" not in spec:
        spec["metadata"] = {
            "title": "Generated UI",
            "description": "UI generated from description"
        }
    
    return spec

@router.get("/templates")
async def get_component_templates():
    """Get available component templates"""
    return {
        "templates": COMPONENT_TEMPLATES,
        "categories": {
            "input": ["input", "form"],
            "display": ["text", "image", "chart", "table"],
            "layout": ["container", "card"],
            "action": ["button", "list"]
        }
    }

@router.post("/validate")
async def validate_a2ui_spec(spec: Dict[str, Any]):
    """Validate an A2UI specification"""
    try:
        # Basic validation
        if "version" not in spec:
            return {"valid": False, "errors": ["Missing version"]}
        
        if "components" not in spec:
            return {"valid": False, "errors": ["Missing components"]}
        
        # Validate component structure
        errors = []
        
        def check_component(component: Dict[str, Any], path: str = ""):
            if "type" not in component:
                errors.append(f"{path}Missing component type")
                return
            
            if component["type"] not in COMPONENT_TEMPLATES:
                errors.append(f"{path}Unknown component type: {component['type']}")
            
            if "children" in component:
                for i, child in enumerate(component["children"]):
                    check_component(child, f"{path}children[{i}].")
        
        for i, component in enumerate(spec["components"]):
            check_component(component, f"components[{i}].")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }

@router.post("/enhance")
async def enhance_a2ui_spec(spec: Dict[str, Any], enhancements: Dict[str, Any]):
    """Enhance an A2UI specification with additional features"""
    try:
        enhanced_spec = spec.copy()
        
        # Apply enhancements
        if "addAccessibility" in enhancements and enhancements["addAccessibility"]:
            # Add accessibility props
            def add_a11y(component: Dict[str, Any]):
                if "props" not in component:
                    component["props"] = {}
                
                # Add ARIA labels
                if component["type"] == "button":
                    component["props"]["ariaLabel"] = component["props"].get("label", "Button")
                elif component["type"] == "input":
                    component["props"]["ariaLabel"] = component["props"].get("placeholder", "Input field")
                
                # Recursively enhance children
                if "children" in component:
                    for child in component["children"]:
                        add_a11y(child)
            
            for component in enhanced_spec["components"]:
                add_a11y(component)
        
        if "addAnimations" in enhancements and enhancements["addAnimations"]:
            # Add animation props
            def add_animations(component: Dict[str, Any]):
                if "props" not in component:
                    component["props"] = {}
                
                component["props"]["animation"] = "fadeIn"
                component["props"]["duration"] = "300ms"
                
                if "children" in component:
                    for child in component["children"]:
                        add_animations(child)
            
            for component in enhanced_spec["components"]:
                add_animations(component)
        
        if "addStyling" in enhancements and enhancements["addStyling"]:
            # Add styling props
            style_theme = enhancements.get("styleTheme", "modern")
            
            def add_styling(component: Dict[str, Any]):
                if "props" not in component:
                    component["props"] = {}
                
                if style_theme == "modern":
                    component["props"]["borderRadius"] = "8px"
                    component["props"]["boxShadow"] = "0 2px 4px rgba(0,0,0,0.1)"
                elif style_theme == "minimal":
                    component["props"]["borderRadius"] = "0"
                    component["props"]["border"] = "1px solid #e0e0e0"
                
                if "children" in component:
                    for child in component["children"]:
                        add_styling(child)
            
            for component in enhanced_spec["components"]:
                add_styling(component)
        
        return {
            "spec": enhanced_spec,
            "enhancements": enhancements
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
