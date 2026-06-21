import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

def get_api_key(provider: str) -> str:
    env_keys = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'gemini': 'GEMINI_API_KEY',
        'opencode': 'OPENCODE_API_KEY'
    }
    env_var = env_keys.get(provider)
    if env_var and os.environ.get(env_var):
        return os.environ.get(env_var)
    
    settings_paths = {
        'anthropic': os.path.join(project_root, '.claude', 'settings.local.json'),
        'gemini': os.path.join(project_root, '.gemini', 'settings.local.json'),
        'opencode': os.path.join(project_root, '.opencode', 'settings.local.json')
    }
    
    path = settings_paths.get(provider)
    if path and os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                parsed = json.load(f)
                
                def find_key(d, target_key):
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if k.lower() == target_key.lower() and isinstance(v, str):
                                return v
                            res = find_key(v, target_key)
                            if res: return res
                    elif isinstance(d, list):
                        for item in d:
                            res = find_key(item, target_key)
                            if res: return res
                    return None
                
                key_names = {
                    'anthropic': ['ANTHROPIC_API_KEY', 'x-api-key', 'apiKey'],
                    'gemini': ['GEMINI_API_KEY', 'apiKey'],
                    'opencode': ['OPENCODE_API_KEY', 'apiKey']
                }
                for kn in key_names.get(provider, []):
                    res = find_key(parsed, kn)
                    if res:
                        return res
        except Exception as e:
            logger.warning(f"Failed to read settings for {provider}: {e}")
            
    return ""

def fetch_anthropic_models() -> List[Dict[str, Any]]:
    api_key = get_api_key('anthropic')
    if not api_key:
        logger.warning("No Anthropic API key found, returning mock data")
        return [
            {"id": "claude-3-5-sonnet-20240620", "name": "Claude 3.5 Sonnet", "provider": "anthropic", "tier": "Advanced"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "provider": "anthropic", "tier": "Expensive"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "provider": "anthropic", "tier": "Normal"}
        ]
        
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = []
            for model in data.get("data", []):
                model_id = model.get("id")
                model_name = model.get("display_name") or model_id
                tier = "Advanced" if "sonnet" in model_id else "Expensive" if "opus" in model_id else "Normal"
                models.append({
                    "id": model_id,
                    "name": model_name,
                    "provider": "anthropic",
                    "tier": tier
                })
            return models
    except Exception as e:
        logger.error(f"Failed to fetch Anthropic models: {e}")
        return []

def fetch_gemini_models() -> List[Dict[str, Any]]:
    api_key = get_api_key('gemini')
    if not api_key:
        logger.warning("No Gemini API key found, returning mock data")
        return [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "gemini", "tier": "Advanced"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "gemini", "tier": "Normal"}
        ]
        
    import urllib.request
    try:
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = []
            for model in data.get("models", []):
                model_id = model.get("name", "")
                if model_id.startswith("models/"):
                    model_id = model_id[7:]
                model_name = model.get("displayName") or model_id
                tier = "Advanced" if "pro" in model_id.lower() else "Normal"
                models.append({
                    "id": model_id,
                    "name": model_name,
                    "provider": "gemini",
                    "tier": tier
                })
            return models
    except Exception as e:
        logger.error(f"Failed to fetch Gemini models: {e}")
        return []

def fetch_opencode_models() -> List[Dict[str, Any]]:
    api_key = get_api_key('opencode')
    if not api_key:
        logger.warning("No OpenCode API key found, returning mock data")
        return [
            {"id": "opencode-go-large", "name": "OpenCode Go Large", "provider": "opencode", "tier": "Advanced"},
            {"id": "opencode-go-small", "name": "OpenCode Go Small", "provider": "opencode", "tier": "Normal"}
        ]
        
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.opencode.ai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                model_name = model_id.split("/")[-1].replace("-", " ")
                tier = "Advanced" if "70B" in model_name or "large" in model_name.lower() else "Normal"
                models.append({
                    "id": model_id,
                    "name": model_name,
                    "provider": "opencode",
                    "tier": tier
                })
            return models
    except Exception as e:
        logger.error(f"Failed to fetch OpenCode models: {e}")
        return []

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
