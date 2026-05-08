"""Lightweight secrets detection for sync.py generated files.

Built-in patterns cover common cases (API keys, tokens, passwords).
Projects can extend detection via security.secret-patterns in project.yaml:

    security:
      secret-patterns:
        - name: "my-service-token"
          regex: "my_[a-zA-Z0-9]{32}"
"""

import re

_SECRET_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{48}', "OpenAI-style API key"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
    (r'ghs_[a-zA-Z0-9]{36}', "GitHub server-to-server token"),
    (r'AKIA[0-9A-Z]{16}', "AWS access key ID"),
    (r'[A-Za-z0-9+/]{40}(?:[A-Za-z0-9+/]{0,2}={0,2})', None),  # broad base64 — filtered below
    (r'anthropic-[a-zA-Z0-9\-_]{40,}', "Anthropic API key"),
    (r'(?i)api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', "Generic API key assignment"),
    (r'(?i)secret\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', "Generic secret assignment"),
    (r'(?i)token\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', "Generic token assignment"),
    (r'(?i)password\s*[:=]\s*["\']?.{8,}', "Generic password assignment"),
    # Bearer tokens: JWT format (eyJ...) used by Home Assistant, Keycloak, etc.
    (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', "JWT / Bearer token"),
    # InfluxDB tokens: long base64url strings (typically 86+ chars ending with ==)
    (r'[a-zA-Z0-9_\-]{80,}={0,2}', "InfluxDB-style long token"),
]

# Patterns that are clearly safe (variables, examples, placeholders)
_SAFE_PATTERNS = [
    r'\{\{[A-Z0-9_]+\}\}',       # {{PLACEHOLDER}}
    r'\$\{[A-Z0-9_]+\}',         # ${ENV_VAR}
    r'<[A-Z_]+>',                 # <PLACEHOLDER>
    r'your[_-]',                  # your_api_key
    r'example',
    r'placeholder',
    r'changeme',
    r'<your',
]


def _is_safe(value: str) -> bool:
    for pat in _SAFE_PATTERNS:
        if re.search(pat, value, re.IGNORECASE):
            return True
    return False


def _load_project_patterns(config: dict) -> list[tuple[str, str]]:
    """Load custom secret patterns from project.yaml security.secret-patterns."""
    patterns = []
    for entry in config.get("security", {}).get("secret-patterns", []):
        regex = entry.get("regex")
        name = entry.get("name", "Custom pattern")
        if regex:
            patterns.append((regex, name))
    return patterns


def scan_for_secrets(content: str, config: dict | None = None) -> list[str]:
    """Return list of human-readable warnings for potential secrets found in content.

    Only flags high-confidence patterns to avoid false positives.
    Skips lines that look like placeholders or documentation examples.

    config: optional project config dict — extends detection with
            security.secret-patterns entries from project.yaml.
    """
    all_patterns = list(_SECRET_PATTERNS)
    if config:
        all_patterns.extend(_load_project_patterns(config))

    findings = []
    for pattern, label in all_patterns:
        if label is None:
            continue  # skip the broad base64 pattern — too noisy
        for match in re.finditer(pattern, content):
            value = match.group(0)
            if not _is_safe(value):
                findings.append(label)
                break  # one warning per pattern type is enough
    return findings
