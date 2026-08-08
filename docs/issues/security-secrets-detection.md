---
title: "[security] Add secrets detection to sync.py generated files"
labels: [security, sync.py, P1]
---

## Summary
`sync.py` copies and generates files without scanning for secrets (API keys, tokens, passwords). A user could accidentally commit sensitive data.

## Risk Scenarios
1. `model-overrides` in `project.yaml` could contain full API endpoint URLs with embedded keys
2. Generated `.claude/settings.json` might contain hardcoded tokens
3. `CLAUDE.personal.md` (gitignored, but adjacent files might reference it)

## Proposed Solution
Add lightweight regex scanning in `sync.py` before writing files:
```python
_SECRET_PATTERNS = [
    r'sk-[a-zA-Z0-9]{48}',           # OpenAI-style key
    r'ghp_[a-zA-Z0-9]{36}',          # GitHub PAT
    r'AKIA[0-9A-Z]{16}',              # AWS Access Key
    r'[a-zA-Z0-9_-]*api[_-]?key[a-zA-Z0-9_-]*[:=]\s*["\']?[a-zA-Z0-9]{16,}',  # generic
]

def _contains_secrets(content: str) -> list[str]:
    found = []
    for pattern in _SECRET_PATTERNS:
        if re.search(pattern, content):
            found.append(pattern)
    return found
```

## Acceptance Criteria
- [ ] Secret patterns defined in `scripts/lib/secrets.py`
- [ ] `sync.py` warns (not fails) when potential secrets detected
- [ ] Warning includes file path and line number
- [ ] Can be disabled via config: `security.scan-secrets: false`

