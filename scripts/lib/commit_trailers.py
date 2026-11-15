"""Commit-trailer contract (E-19): validate and render ``commit.trailers``.

Pure stdlib; the sync path must not depend on jsonschema. Messages are
prefixed with ``commit.`` so they are greppable in ``--validate`` output.
"""
import re
from typing import List

_TRAILER_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*: \S.*")
_EMAIL_RE = re.compile(r"<[^<>]*@[^<>]*>")
_KNOWN_KEYS = frozenset({"trailers"})


def _valid(item: object) -> bool:
    return isinstance(item, str) and _TRAILER_RE.fullmatch(item) is not None


def _trailer_list(cfg: dict) -> list:
    block = (cfg or {}).get("commit") if isinstance(cfg, dict) else None
    if not isinstance(block, dict):
        return []
    items = block.get("trailers")
    return items if isinstance(items, list) else []


def commit_violations(cfg: dict) -> List[str]:
    """Schema violations of the ``commit`` block; missing/None block is valid."""
    block = cfg.get("commit") if isinstance(cfg, dict) else None
    if block is None:
        return []
    if not isinstance(block, dict):
        return ["commit must be a mapping"]
    out: List[str] = []
    unknown = sorted(str(k) for k in block if k not in _KNOWN_KEYS)
    if unknown:
        out.append(f"commit has unknown key(s): {', '.join(unknown)}")
    trailers = block.get("trailers", [])
    if not isinstance(trailers, list):
        out.append("commit.trailers must be a list")
        return out
    for i, item in enumerate(trailers):
        if not _valid(item):
            out.append(f"commit.trailers[{i}] must match 'Token: value'")
    dupes = sorted({t for t in trailers if isinstance(t, str) and trailers.count(t) > 1})
    if dupes:
        out.append(f"commit.trailers contains duplicate value(s): {', '.join(dupes)}")
    return out


def commit_warnings(cfg: dict) -> List[str]:
    """Co-Authored-By items without an email address; never raises."""
    out: List[str] = []
    for i, item in enumerate(_trailer_list(cfg)):
        if not _valid(item):
            continue
        token, value = item.split(": ", 1)
        if token.lower() == "co-authored-by" and not _EMAIL_RE.search(value):
            out.append(f"commit.trailers[{i}] Co-Authored-By should include an email address")
    return out


def render_commit_trailers(cfg: dict) -> str:
    """Valid, de-duplicated trailers joined by newline; '' if none; never raises."""
    seen: List[str] = []
    for item in _trailer_list(cfg):
        if _valid(item) and item not in seen:
            seen.append(item)
    return "\n".join(seen)
