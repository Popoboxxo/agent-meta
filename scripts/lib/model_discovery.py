import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def fetch_anthropic_models() -> List[Dict[str, Any]]:
    # Mock implementation for tests
    return [
        {"id": "claude-3-5-sonnet-20240620", "provider": "anthropic", "tier": "Advanced"},
        {"id": "claude-3-opus-20240229", "provider": "anthropic", "tier": "Expensive"},
        {"id": "claude-3-haiku-20240307", "provider": "anthropic", "tier": "Normal"}
    ]

def fetch_gemini_models() -> List[Dict[str, Any]]:
    # Mock implementation
    return [
        {"id": "gemini-1.5-pro", "provider": "gemini", "tier": "Advanced"},
        {"id": "gemini-1.5-flash", "provider": "gemini", "tier": "Normal"}
    ]

def fetch_opencode_models() -> List[Dict[str, Any]]:
    # Mock implementation
    return [
        {"id": "opencode-go-large", "provider": "opencode", "tier": "Advanced"},
        {"id": "opencode-go-small", "provider": "opencode", "tier": "Normal"}
    ]

def discover_models() -> Dict[str, Any]:
    logger.info("Discovering models from providers...")
    models = []
    models.extend(fetch_anthropic_models())
    models.extend(fetch_gemini_models())
    models.extend(fetch_opencode_models())
    
    registry = {
        "models": models
    }
    
    # Calculate absolute path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    registry_path = os.path.join(project_root, 'config', 'generated', 'model-registry.json')
    
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
        
    logger.info(f"Model registry updated at {registry_path}")
    return registry

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    discover_models()
