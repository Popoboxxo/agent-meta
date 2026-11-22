"""Commit-trailer contract (E-19): validate and render ``commit.trailers``.

Pure stdlib; the sync path must not depend on jsonschema. Messages are
prefixed with ``commit.`` so they are greppable in ``--validate`` output.
"""
import re
from typing import List, Tuple

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


def _footer_lines(message: str) -> List[str]:
    """Footer paragraph lines of a message whose CRLF is already normalised.

    Comment ('#') lines are dropped and trailing whitespace is stripped per
    line. A message with fewer than two paragraphs has no footer (a one-liner)
    and yields an empty list.
    """
    kept: List[str] = []
    for raw in message.split("\n"):
        if raw.lstrip().startswith("#"):
            continue
        kept.append(raw.rstrip())
    paragraphs: List[List[str]] = []
    current: List[str] = []
    for line in kept:
        if not line.strip():
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(current)
    return paragraphs[-1] if len(paragraphs) > 1 else []


def check_commit_message(message: str, cfg: dict) -> Tuple[List[str], List[str]]:
    """Check a commit message against the configured ``commit.trailers``.

    Pure and never raises. Returns ``(errors, warnings)``. Expected trailers
    come from :func:`render_commit_trailers`; an empty contract is a no-op.
    Only the footer (the last paragraph after comment lines and trailing
    whitespace are removed) is inspected, with verbatim token spelling.
    """
    errors: List[str] = []
    warnings: List[str] = []
    rendered = render_commit_trailers(cfg)
    if not rendered:
        return errors, warnings
    if not isinstance(message, str):
        message = ""
    if message.startswith("\ufeff"):
        errors.append("commit message starts with a UTF-8 BOM")
        message = message[1:]
    footer = _footer_lines(message.replace("\r\n", "\n"))
    for expected in rendered.split("\n"):
        token = expected.split(":", 1)[0]
        token_lines = [line for line in footer if line.startswith(token + ":")]
        if not token_lines:
            errors.append("commit trailer missing: " + expected)
        elif footer.count(expected) > 1:
            errors.append("commit trailer duplicated: " + expected)
        elif footer.count(expected) == 0:
            warnings.append(
                "commit trailer token '%s' has a different value (brief override?)"
                % token
            )
    return errors, warnings
