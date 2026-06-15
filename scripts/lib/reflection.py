"""Reflection-Loop configuration management."""

import os
import sys

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _require_yaml() -> None:
    """Abort with a clear message when PyYAML is not installed."""
    if not _YAML_AVAILABLE:
        print(
            "ERROR: PyYAML not installed but required for reflection configuration. "
            "Run: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)


def load_reflection_pairs(config_dir=None):
    """Load reflection pairs from role-defaults.yaml."""
    _require_yaml()
    if config_dir is None:
        config_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
    defaults_path = os.path.join(config_dir, 'role-defaults.yaml')
    with open(defaults_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('reflection_pairs', [])


def load_project_overrides(project_config=None):
    """Load project-specific overrides from project.yaml."""
    _require_yaml()
    if project_config is None:
        project_config = os.path.join(os.path.dirname(__file__), '..', '..', '.meta-config', 'project.yaml')
    if not os.path.exists(project_config):
        return {}
    with open(project_config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config.get('reflection-pairs', {}).get('overrides', {})


def apply_project_overrides(pairs, overrides):
    """Merge project overrides into reflection pairs."""
    result = []
    for pair in pairs:
        pair_id = pair.get('id')
        if pair_id in overrides:
            override = overrides[pair_id]
            merged = {**pair, **override}
            if not merged.get('enabled', True):
                continue  # Skip disabled pairs
            merged.pop('enabled', None)  # Remove internal flag
            result.append(merged)
        else:
            result.append(pair)
    return result


def validate_reflection_pairs(pairs, available_roles):
    """Validate that generator and critic roles exist."""
    errors = []
    for pair in pairs:
        gen = pair.get('generator')
        crit = pair.get('critic')
        if gen not in available_roles:
            errors.append(f"Reflection pair '{pair['id']}': generator '{gen}' not found in available roles")
        if crit not in available_roles:
            errors.append(f"Reflection pair '{pair['id']}': critic '{crit}' not found in available roles")
    return errors


def inject_loop_config(template_content, pair_config):
    """Inject reflection loop placeholders into template content."""
    replacements = {
        '{{MAX_ITERATIONS}}': str(pair_config.get('max_iterations', 3)),
        '{{CRITIC_NAME}}': pair_config.get('critic', 'unknown'),
        '{{GENERATOR_NAME}}': pair_config.get('generator', 'unknown'),
        '{{PAIR_ID}}': pair_config.get('id', 'unknown'),
        '{{ON_BLOCKED}}': pair_config.get('on_blocked', 'escalate_to_orchestrator'),
    }
    result = template_content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def get_reflection_pairs_for_role(role, pairs):
    """Get all reflection pairs where the given role is generator or critic."""
    return [p for p in pairs if p.get('generator') == role or p.get('critic') == role]
