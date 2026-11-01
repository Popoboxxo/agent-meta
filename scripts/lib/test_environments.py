"""Validation of the ``test-environments`` project block (issue #1089).

``test-environments`` declares per-project test/dev *targets* (local, remote or
both). It is NOT to be confused with ``environments`` (env-var definitions):
a ``token-env`` entry must reference an ``environments`` entry with
``secret: true``; the token value itself never appears in ``project.yaml``.

The JSON schema (``config/project-config.schema.json``) is a warning-only
addition; this module is the hard check executed from the config load path.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlsplit

from . import platform
from .io import load_yaml_file
from .log import SyncLog

KINDS = ("local", "remote", "both")
ACCESS_LEVELS = ("read", "deploy")
REMOTE_ACCESS = ("deny", "ask", "allow")
DEFAULTS = {"kind": "local", "access": "read", "remote-access": "ask"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TOKEN_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

_BLOCK_KEY = "test-environments"
_ENTRY_KEYS = ("kind", "url", "token-env", "access", "remote-access", "notes")
_REMOTE_KINDS = ("remote", "both")
#: Fallback precedence for URL-less remote targets (spec §10.2, HACS > HA).
FALLBACK_PLATFORM_KEYS = (
    "platform.hacs.dev_instance_url",
    "platform.homeassistant.ha_url",
)
_ENUM_FIELDS = (
    ("kind", KINDS),
    ("access", ACCESS_LEVELS),
    ("remote-access", REMOTE_ACCESS),
)


def _astype(value: Any) -> str:
    return type(value).__name__


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def check_test_environments(config: dict) -> Tuple[List[str], List[str]]:
    """Return ``(errors, warnings)`` for the ``test-environments`` block.

    ``None`` and ``{}`` are "unconfigured" and produce no findings (RF1); a
    non-mapping block is a hard error. Error paths use
    ``test-environments.<name>.<key>: <message>`` (block level:
    ``test-environments: <message>``).
    """
    errors: List[str] = []
    warnings: List[str] = []

    block = config.get(_BLOCK_KEY)
    if block is None:
        return errors, warnings
    if not isinstance(block, dict):
        errors.append(
            f"{_BLOCK_KEY}: expected a mapping, got {_astype(block)}"
        )
        return errors, warnings

    for name, entry in sorted(block.items(), key=lambda kv: str(kv[0])):
        if not isinstance(name, str) or not NAME_RE.match(name):
            errors.append(
                f"{_BLOCK_KEY}: invalid environment name {name!r} "
                f"(expected ^[a-z0-9][a-z0-9-]*$)"
            )
            continue

        prefix = f"{_BLOCK_KEY}.{name}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: expected a mapping, got {_astype(entry)}")
            continue

        for key in sorted(entry, key=str):
            if key not in _ENTRY_KEYS:
                errors.append(f"{prefix}.{key}: unknown key")

        for key, allowed in _ENUM_FIELDS:
            if key not in entry:
                continue
            value = entry[key]
            if isinstance(value, bool):
                errors.append(
                    f"{prefix}.{key}: must be a quoted string, quote the value "
                    f"(got bool {_bool_text(value)})"
                )
            elif not isinstance(value, str) or value not in allowed:
                errors.append(
                    f"{prefix}.{key}: invalid value {value!r} "
                    f"(allowed: {', '.join(allowed)})"
                )

        if "url" in entry:
            url = entry["url"]
            if not isinstance(url, str) or not url.strip():
                errors.append(f"{prefix}.url: url must be a non-empty string")
            elif "{{" in url or "}}" in url:
                errors.append(f"{prefix}.url: placeholder syntax not allowed")
            elif "@" in urlsplit(url).netloc:
                errors.append(f"{prefix}.url: url must not contain userinfo")

        if "notes" in entry:
            notes = entry["notes"]
            if not isinstance(notes, str):
                errors.append(f"{prefix}.notes: notes must be a string")
            elif "{{" in notes or "}}" in notes:
                errors.append(f"{prefix}.notes: placeholder syntax not allowed")

        _check_token_env(config, prefix, entry, errors, warnings)
        warnings.extend(_warn_ineffective_settings(prefix, entry))

    return errors, warnings


def _check_token_env(
    config: dict,
    prefix: str,
    entry: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    """Rule 3: ``token-env`` names an ``environments`` entry with ``secret: true``.

    Only the boolean ``True`` counts as secret (RF3); a string ``"true"`` or
    ``1`` is rejected. A missing/non-mapping ``environments`` block reports
    "not defined" instead of crashing.
    """
    if "token-env" not in entry:
        return
    token = entry["token-env"]
    path = f"{prefix}.token-env"
    if not isinstance(token, str) or not TOKEN_ENV_RE.match(token):
        errors.append(f"{path}: expected env var NAME, not a value (got {token!r})")
        return

    environments = config.get("environments")
    if not isinstance(environments, dict) or token not in environments:
        errors.append(f"{path}: environments entry '{token}' not defined")
        return
    definition = environments[token]
    if not isinstance(definition, dict) or definition.get("secret") is not True:
        errors.append(f"{path}: environments entry '{token}' must have secret: true")
        return
    default = definition.get("default")
    if str(default or "").strip():
        warnings.append(
            f"environments entry '{token}' has a non-empty default "
            f"(secret value in project.yaml)"
        )


def _warn_ineffective_settings(prefix: str, entry: Dict[str, Any]) -> List[str]:
    """Warning-only semantics from spec §9.4 rules 4, 5 and 7."""
    warnings: List[str] = []
    kind = entry.get("kind", DEFAULTS["kind"])
    access = entry.get("access", DEFAULTS["access"])
    remote_access = entry.get("remote-access", DEFAULTS["remote-access"])

    if not isinstance(kind, str) or kind not in KINDS:
        return warnings

    if kind == "local":
        if "url" in entry:
            warnings.append(f"{prefix}: kind: local ignores url")
        if "remote-access" in entry:
            warnings.append(f"{prefix}: kind: local ignores remote-access")
        if access == "deploy":
            warnings.append(f"{prefix}: access: deploy has no effect for kind: local")
    elif access == "deploy" and remote_access == "deny":
        warnings.append(
            f"{prefix}: access: deploy conflicts with remote-access: deny (deny wins)"
        )
    return warnings


def collect_test_environment_errors(config: dict) -> List[str]:
    """Non-exiting entry point, reused by the admin-server section guard."""
    errors, _ = check_test_environments(config)
    return errors


def validate_test_environments(config: dict, config_path: Path) -> None:
    """Hard-fail the config load on invalid ``test-environments`` entries.

    Errors are printed as ``ERROR: <config_path>: <message>`` and terminate
    with exit code 1; warnings are printed as ``WARN: ...`` without exiting.
    """
    errors, warnings = check_test_environments(config)
    for warning in warnings:
        print(f"WARN: {config_path}: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"ERROR: {config_path}: {error}", file=sys.stderr)
        sys.exit(1)


def load_project_platform_vars(project_root: Path) -> dict:
    """Return the *project-layer* platform variables as flat ``platform.*`` keys.

    Only ``.claude/platform-config.yaml`` is read — never the merged defaults,
    so a default like ``homeassistant.ha_url`` can never trigger a fallback on
    its own (spec §10.2). A missing, unreadable or malformed file yields ``{}``.
    """
    path = project_root / platform.CLAUDE_PLATFORM_CONFIG
    data = load_yaml_file(path, on_error="default", default={})
    if not isinstance(data, dict):
        return {}
    return {
        key: value
        for key, value in platform._flatten_yaml_dict(data).items()
        if key.startswith("platform.")
    }


def _fallback_url(block: dict, project_vars: dict) -> Tuple[Any, str]:
    """Pick the platform fallback URL for exactly one URL-less remote target.

    Conditions (all required): exactly one ``kind`` in {remote, both} entry
    without ``url``, a non-empty project-layer platform value, and the
    precedence ``hacs.dev_instance_url`` > ``homeassistant.ha_url``.
    """
    urlless = [
        name
        for name, entry in block.items()
        if isinstance(entry, dict)
        and entry.get("kind") in _REMOTE_KINDS
        and not entry.get("url")
    ]
    if len(urlless) != 1:
        return None, ""
    for key in FALLBACK_PLATFORM_KEYS:
        value = project_vars.get(key)
        if isinstance(value, str) and value.strip():
            return value, key
    return None, ""


def resolve_test_environments(
    config: dict, platform_project_vars: "Dict[str, Any] | None"
) -> "Dict[str, Dict[str, Any]]":
    """Resolve every ``test-environments`` entry with defaults and URL.

    Returns one dict per environment with the keys ``kind``, ``url`` (or
    ``None``), ``url_source`` (``"config"``, a ``platform.*`` key or ``""``),
    ``token-env``, ``access``, ``remote-access`` and ``notes``. Broken input
    never raises or exits: it yields ``{}`` plus one warning (IC-3).
    """
    errors, _ = check_test_environments(config)
    if errors:
        SyncLog().warning(
            "test-environments: invalid block ignored for resolution: "
            + "; ".join(errors)
        )
        return {}
    block = config.get(_BLOCK_KEY)
    if not isinstance(block, dict):
        return {}

    project_vars = platform_project_vars or {}
    fallback_url, fallback_source = _fallback_url(block, project_vars)
    resolved: Dict[str, Dict[str, Any]] = {}
    for name, entry in sorted(block.items(), key=lambda kv: str(kv[0])):
        kind = entry.get("kind", DEFAULTS["kind"])
        url = entry.get("url")
        url_source = "config" if url else ""
        if not url and kind in _REMOTE_KINDS and fallback_url is not None:
            url, url_source = fallback_url, fallback_source
        resolved[name] = {
            "kind": kind,
            "url": url,
            "url_source": url_source,
            "token-env": entry.get("token-env"),
            "access": entry.get("access", DEFAULTS["access"]),
            "remote-access": entry.get("remote-access", DEFAULTS["remote-access"]),
            "notes": entry.get("notes") or "",
        }
    return resolved


_TABLE_HEADER = (
    "| Name | kind | URL / source | access | remote-access | notes |",
    "|---|---|---|---|---|---|",
)
_DISTINCTION = (
    "- `environments:` defines environment variables; `test-environments:` "
    "defines targets. `token-env` only references an `environments:` entry."
)
_CONVENTION = (
    "Access approval is a prompt convention (convention boundary), not a "
    "technical barrier."
)
_KIND_RULES = {
    "local": "- **local:** local tests and dev stack only; no remote access.",
    "remote": "- **remote:** the remote environment is the test target; access "
    "only as allowed by remote-access and access.",
    "both": "- **both:** test locally first, then the remote environment only "
    "after approval as required by its remote-access.",
}
_ACCESS_RULES = {
    "read": "- **access read:** read/query only (status, logs, config check); "
    "never write or deploy.",
    "deploy": "- **access deploy:** may also roll out or change things, only "
    "together with remote-access ask or allow (deny always wins).",
}
_REMOTE_ACCESS_RULES = {
    "deny": "- **remote-access deny:** never contact the environment (ssh, "
    "scp, curl, `docker -H`, deploy); if the task needs it, report it to "
    "main_chat.",
    "allow": "- **remote-access allow:** access is permitted within the access "
    "level; still report every deploy in your result.",
    "ask": "- **remote-access ask:** stop BEFORE the first remote access (ssh, "
    "scp, curl, `docker -H`, deploy). Return `STATUS: partial` with "
    "`APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>`. The "
    "orchestrator obtains the user's approval and re-dispatches with "
    "`APPROVED: env=<name>; action=<action>` in the task. The approval "
    "applies only to the named environment and action; every further action "
    "needs a new APPROVAL_REQUEST. Record the approval in your report.",
}
_TARGET_RULE = (
    "- If the target or its URL is unclear, return `STATUS: partial` with "
    "`APPROVAL_REQUEST: target?` and ask main_chat."
)


def _cell(value: Any) -> str:
    """Sanitise one table cell: newlines become spaces, ``|`` is escaped (RF4)."""
    text = str(value)
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return text.replace("|", "\\|")


def _url_cell(env: Dict[str, Any]) -> str:
    url = env.get("url")
    if url:
        source = env.get("url_source") or ""
        if source and source != "config":
            return f"{url} (from {source})"
        return str(url)
    if env.get("kind") in _REMOTE_KINDS:
        return "URL not configured"
    return "\u2014"


def _secret_hint(name: str, token: str) -> str:
    return (
        f"- **Token for `{name}`:** env var `${{{token}}}`; the value comes "
        "from the shell environment, provided via `source .meta-config/env.sh` "
        f"(from the `environments:` entry `{token}` with `secret: true`, "
        "masked). Never print, log or write the value, and never read it from "
        f"files; use `${{{token}}}` in the shell only."
    )


def render_test_environment_block(resolved: dict) -> str:
    """Render the role-agnostic Markdown block (IC-4, spec §10.4).

    ``{}`` renders as ``""``. Environments are sorted by name; the block has
    no trailing newline and contains no role-specific logic (b12/C2).
    """
    if not resolved:
        return ""
    names = sorted(resolved)
    lines = ["## Test environments", "", _DISTINCTION, ""]
    lines.extend(_TABLE_HEADER)
    for name in names:
        env = resolved[name]
        kind = env.get("kind", DEFAULTS["kind"])
        is_local = kind == "local"
        cells = [
            name,
            kind,
            _url_cell(env),
            "\u2014" if is_local else env.get("access", DEFAULTS["access"]),
            "\u2014" if is_local else env.get("remote-access", DEFAULTS["remote-access"]),
            env.get("notes") or "\u2014",
        ]
        lines.append("| " + " | ".join(_cell(cell) for cell in cells) + " |")
    lines.extend(["", _CONVENTION, ""])

    kinds = {resolved[name].get("kind", DEFAULTS["kind"]) for name in names}
    for kind in KINDS:
        if kind in kinds:
            lines.append(_KIND_RULES[kind])

    remote_envs = [
        resolved[name]
        for name in names
        if resolved[name].get("kind", DEFAULTS["kind"]) in _REMOTE_KINDS
    ]
    accesses = {env.get("access", DEFAULTS["access"]) for env in remote_envs}
    for level in ACCESS_LEVELS:
        if level in accesses:
            lines.append(_ACCESS_RULES[level])
    remote_accesses = {
        env.get("remote-access", DEFAULTS["remote-access"]) for env in remote_envs
    }
    for mode in REMOTE_ACCESS:
        if mode in remote_accesses:
            lines.append(_REMOTE_ACCESS_RULES[mode])

    if len(names) > 1 or any(not env.get("url") for env in remote_envs):
        lines.append(_TARGET_RULE)

    secrets = [
        (name, resolved[name]["token-env"])
        for name in names
        if resolved[name].get("token-env")
    ]
    if secrets:
        lines.append("")
        lines.extend(_secret_hint(name, token) for name, token in secrets)

    return "\n".join(lines)


def build_test_environment_variables(
    config: dict, project_root: "Path | None"
) -> Dict[str, str]:
    """Build the two template variables for the gated test-environment block.

    ``TEST_ENVIRONMENT_BLOCK`` carries the rendered Markdown block (empty when
    unconfigured) and ``TEST_ENVIRONMENTS_SET`` is ``"true"`` as soon as at
    least one environment resolves, so the ``{{#if}}`` gate opens. The platform
    fallback URL is only read when ``project_root`` is given.
    """
    project_vars = load_project_platform_vars(project_root) if project_root else None
    resolved = resolve_test_environments(config, project_vars)
    return {
        "TEST_ENVIRONMENT_BLOCK": render_test_environment_block(resolved),
        "TEST_ENVIRONMENTS_SET": "true" if resolved else "false",
    }
