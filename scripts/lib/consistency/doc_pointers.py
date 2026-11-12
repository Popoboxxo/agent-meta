"""``context.dangling-doc-pointer``: generated artifacts naming a ``docs/*.md`` file that is not delivered (#1180)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping, Sequence

from . import context_budget as cb

_DOC_POINTER_RE = re.compile(r"`(docs/[^`\s]+\.md)`")


def check_dangling_doc_pointer(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """WARNING per backticked ``docs/...md`` path in a generated artifact that does not exist under *project_root*."""
    root = Path(project_root)
    findings, seen = [], set()
    for provider in active_providers:
        for artifact in cb._pointer_artifacts(root, capabilities.get(provider) or {}):
            text = cb._read_text(artifact)
            if text is None:
                continue
            rel = cb._rel(artifact, root)
            for doc in sorted(set(_DOC_POINTER_RE.findall(text))):
                if (rel, doc) in seen or (root / doc).is_file():
                    continue
                seen.add((rel, doc))
                findings.append(cb._warn(
                    "context.dangling-doc-pointer", rel,
                    f"{provider}: points to {doc} which does not exist in the project",
                    "inline the core statement into the rule instead of linking framework docs"))
    return findings
