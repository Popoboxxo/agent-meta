---
title: "[security] Shell injection risk in hook scripts"
labels: [security, hooks, P1]
---

## Summary
Hook scripts parse JSON input via shell command substitution. If the JSON contains shell metacharacters, arbitrary code execution is possible.

## Affected Code
```bash
# hooks/1-generic/dod-push-check.sh
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))")
```

## Risk
A malicious tool response could inject shell commands through crafted JSON.

## Fix
Replace shell parsing with pure Python stdin reading:
```python
#!/usr/bin/env python3
import json, sys

data = json.load(sys.stdin)
tool_name = data.get('tool_name', '')
# ... logic ...
```

Or keep bash but sanitize:
```bash
TOOL_NAME=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))")
```

## Acceptance Criteria
- [ ] All hook templates use Python for JSON parsing
- [ ] No shell command substitution on untrusted JSON input
- [ ] Security note added to `howto/hooks.md`

## Related
- `docs/reviews/framework-provider-review-2026-05-07.md` — Finding #4
