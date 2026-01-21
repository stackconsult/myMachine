"""
Model Configuration API
Handles multi-model configuration and switching
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/config", tags=["model-config"])

class ModelConfig(BaseModel):
    provider: str
    model: str
    apiKey: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: Optional[float] = 0.7
    maxTokens: Optional[int] = 2048

class ModelTestRequest(BaseModel):
    provider: str
    model: str
    apiKey: Optional[str] = None
    endpoint: Optional[str] = None

# Store model configurations in memory (in production, use database)
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "openai": ModelConfig(
        provider="openai",
        model="gpt-4-turbo",
        apiKey=os.getenv("OPENAI_API_KEY")
    ),
    "anthropic": ModelConfig(
        provider="anthropic",
        model="claude-3-sonnet",
        apiKey=os.getenv("ANTHROPIC_API_KEY")
    ),
    "groq": ModelConfig(
        provider="groq",
        model="mixtral-8x7b-32768",
        apiKey=os.getenv("GROQ_API_KEY")
    ),
    "local": ModelConfig(
        provider="local",
        model="ollama-llama2",
        endpoint="http://localhost:11434"
    )
}

@router.post("/model")
async def save_model_config(config: ModelConfig):
    """Save model configuration"""
    try:
        # Store configuration
        MODEL_CONFIGS[config.provider] = config
        
        # Update environment variables
        if config.provider == "openai" and config.apiKey:
            os.environ["OPENAI_API_KEY"] = config.apiKey
        elif config.provider == "anthropic" and config.apiKey:
            os.environ["ANTHROPIC_API_KEY"] = config.apiKey
        elif config.provider == "groq" and config.apiKey:
            os.environ["GROQ_API_KEY"] = config.apiKey
        
        # Set as default if specified
        os.environ["MODEL_PROVIDER"] = config.provider
        os.environ[f"{config.provider.upper()}_MODEL"] = config.model
        
        return {"success": True, "message": "Configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model")
async def get_model_configs():
    """Get all model configurations"""
    return {
        "configs": MODEL_CONFIGS,
        "current": os.getenv("MODEL_PROVIDER", "openai")
    }

@router.post("/test")
async def test_model_connection(request: ModelTestRequest):
    """Test connection to model provider"""
    try:
        import httpx
        
        if request.provider == "openai":
            # Test OpenAI API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {request.apiKey}"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": "OpenAI connection successful"}
                else:
                    return {"success": False, "error": "Invalid API key"}
        
        elif request.provider == "anthropic":
            # Test Anthropic API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": request.apiKey,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": request.model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}]
                    }
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Anthropic connection successful"}
                else:
                    return {"success": False, "error": "Invalid API key or model"}
        
        elif request.provider == "groq":
            # Test Groq API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {request.apiKey}"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Groq connection successful"}
                else:
                    return {"success": False, "error": "Invalid API key"}
        
        elif request.provider == "local":
            # Test local model endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{request.endpoint}/api/tags")
                if response.status_code == 200:
                    return {"success": True, "message": "Local model connection successful"}
                else:
                    return {"success": False, "error": "Cannot reach local model server"}
        
        else:
            return {"success": False, "error": "Unknown provider"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/models/{provider}")
async def get_available_models(provider: str):
    """Get available models for a provider"""
    try:
        if provider == "openai":
            return {
                "models": [
                    {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
                    {"id": "gpt-4", "name": "GPT-4"},
                    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"}
                ]
            }
        elif provider == "anthropic":
            return {
                "models": [
                    {"id": "claude-3-opus", "name": "Claude 3 Opus"},
                    {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
                    {"id": "claude-3-haiku", "name": "Claude 3 Haiku"}
                ]
            }
        elif provider == "groq":
            return {
                "models": [
                    {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
                    {"id": "llama2-70b-4096", "name": "Llama2 70B"},
                    {"id": "gemma-7b-it", "name": "Gemma 7B"}
                ]
            }
        elif provider == "local":
            # Fetch from Ollama
            import httpx
            config = MODEL_CONFIGS.get("local")
            if config and config.endpoint:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{config.endpoint}/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        models = [
                            {"id": model["name"], "name": model["name"]}
                            for model in data.get("models", [])
                        ]
                        return {"models": models}
            
            # Default local models
            return {
                "models": [
                    {"id": "ollama-llama2", "name": "Ollama Llama2"},
                    {"id": "ollama-mistral", "name": "Ollama Mistral"},
                    {"id": "custom", "name": "Custom Endpoint"}
                ]
            }
        else:
            raise HTTPException(status_code=404, detail="Provider not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/switch/{provider}")
async def switch_model_provider(provider: str):
    """Switch to a different model provider"""
    try:
        if provider not in MODEL_CONFIGS:
            raise HTTPException(status_code=404, detail="Provider not configured")
        
        # Update environment
        os.environ["MODEL_PROVIDER"] = provider
        
        # Update CopilotKit runtime if needed
        # This would require restarting the runtime or using a dynamic adapter
        
        return {
            "success": True,
            "message": f"Switched to {provider}",
            "provider": provider,
            "model": MODEL_CONFIGS[provider].model
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
