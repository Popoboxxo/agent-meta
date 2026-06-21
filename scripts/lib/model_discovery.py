import json
import os
import logging
import urllib.request
import yaml
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OPENCODE_GO_MODELS = [
    {"id": "opencode-go/glm-5.2", "name": "glm-5.2", "provider": "opencode-go", "input_cost_api": 1.40, "output_cost_api": 4.40},
    {"id": "opencode-go/glm-5.1", "name": "glm-5.1", "provider": "opencode-go", "input_cost_api": 1.40, "output_cost_api": 4.40},
    {"id": "opencode-go/kimi-k2.7-code", "name": "kimi-k2.7-code", "provider": "opencode-go", "input_cost_api": 0.95, "output_cost_api": 4.00},
    {"id": "opencode-go/kimi-k2.6", "name": "kimi-k2.6", "provider": "opencode-go", "input_cost_api": 0.95, "output_cost_api": 4.00},
    {"id": "opencode-go/mimo-v2.5", "name": "mimo-v2.5", "provider": "opencode-go", "input_cost_api": 0.14, "output_cost_api": 0.28},
    {"id": "opencode-go/mimo-v2.5-pro", "name": "mimo-v2.5-pro", "provider": "opencode-go", "input_cost_api": 1.74, "output_cost_api": 3.48},
    {"id": "opencode-go/minimax-m3", "name": "minimax-m3", "provider": "opencode-go", "input_cost_api": 0.30, "output_cost_api": 1.20},
    {"id": "opencode-go/minimax-m2.7", "name": "minimax-m2.7", "provider": "opencode-go", "input_cost_api": 0.30, "output_cost_api": 1.20},
    {"id": "opencode-go/minimax-m2.5", "name": "minimax-m2.5", "provider": "opencode-go", "input_cost_api": 0.30, "output_cost_api": 1.20},
    {"id": "opencode-go/qwen3.7-max", "name": "qwen3.7-max", "provider": "opencode-go", "input_cost_api": 2.50, "output_cost_api": 7.50},
    {"id": "opencode-go/qwen3.7-plus", "name": "qwen3.7-plus", "provider": "opencode-go", "input_cost_api": 0.40, "output_cost_api": 1.60},
    {"id": "opencode-go/qwen3.6-plus", "name": "qwen3.6-plus", "provider": "opencode-go", "input_cost_api": 0.50, "output_cost_api": 3.00},
    {"id": "opencode-go/deepseek-v4-pro", "name": "deepseek-v4-pro", "provider": "opencode-go", "input_cost_api": 1.74, "output_cost_api": 3.48},
    {"id": "opencode-go/deepseek-v4-flash", "name": "deepseek-v4-flash", "provider": "opencode-go", "input_cost_api": 0.14, "output_cost_api": 0.28},
]

def fetch_openrouter_models(excluded_models=None) -> List[Dict[str, Any]]:
    if excluded_models is None:
        excluded_models = []
    models = []
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models")
        with urllib.request.urlopen(req, timeout=20) as response:
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
                    provider = "openai"
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
    
    models.extend(OPENCODE_GO_MODELS)
    
    registry = {
        "models": models
    }

    registry_path = os.path.join(project_root, 'config', 'generated', 'model-registry.json')
    
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
        
    logger.info(f"Model registry updated at {registry_path}")
    return registry

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    discover_models()
