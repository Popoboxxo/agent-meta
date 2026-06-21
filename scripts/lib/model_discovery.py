import json
import os
import logging
import urllib.request
import yaml
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def fetch_openrouter_models(excluded_models=None) -> List[Dict[str, Any]]:
    if excluded_models is None:
        excluded_models = []
    models = []
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            for m in data.get("data", []):
                model_id = m.get("id", "")
                if model_id in excluded_models:
                    continue
                model_name = m.get("name") or model_id
                
                if model_id.startswith("anthropic/"):
                    provider = "anthropic"
                elif model_id.startswith("google/"):
                    provider = "gemini"
                elif model_id.startswith("openai/"):
                    provider = "opencode-zen"
                else:
                    provider = "opencode-go"
                
                pricing = m.get("pricing", {})
                
                try:
                    input_cost = float(pricing.get("prompt", 0)) * 1000000
                except (ValueError, TypeError):
                    input_cost = 0.0
                    
                try:
                    output_cost = float(pricing.get("completion", 0)) * 1000000
                except (ValueError, TypeError):
                    output_cost = 0.0
                
                models.append({
                    "id": model_id,
                    "name": model_name,
                    "provider": provider,
                    "input_cost_api": input_cost,
                    "output_cost_api": output_cost,
                    "tier": "Standard" # Fallback if needed by UI
                })
    except Exception as e:
        logger.error(f"Failed to fetch OpenRouter models: {e}")
    return models

def discover_models() -> Dict[str, Any]:
    logger.info("Discovering models from OpenRouter...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    pricing_path = os.path.join(project_root, 'config', 'pricing-overlay.yaml')
    
    excluded_models = []
    try:
        if os.path.exists(pricing_path):
            with open(pricing_path, 'r', encoding='utf-8') as f:
                pricing_data = yaml.safe_load(f) or {}
                excluded_models = pricing_data.get('excluded_models', [])
    except Exception as e:
        logger.error(f"Failed to read pricing-overlay.yaml: {e}")

    models = fetch_openrouter_models(excluded_models)
    
    registry = {
        "models": models
    }
    
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
