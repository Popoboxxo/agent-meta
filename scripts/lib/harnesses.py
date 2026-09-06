"""Harness abstraction for cross-harness dev isolation (issue #547).

A "harness" is one AI coding tool (Claude Code, Opencode, ...) working in its
own top-level Git checkout of a project — deliberately NOT a shared working
directory and NOT a Git worktree (submodule + sync.py breakage risk; see
docs/guides/cross-harness-dev-isolation.md for the checkout/branch
conventions and the rationale).

Harness differences are expressed purely as data: config/harnesses/<name>.yaml
in the agent-meta framework root. Python code never branches on a harness or
provider name — behavior keys off the presence/absence of config fields, the
same capability-flag style as ``_has_capability`` in lib/context.py.

Activation precedence (first wins):
  1. CLI flag ``--harness <name>``
  2. Environment variable ``AGENT_META_HARNESS``
  3. (no project.yaml key — project.yaml is committed and travels with the
     repo across all checkouts, so a project-scoped activation would activate
     the same harness in every checkout and defeat the isolation)

With no harness active every code path here is inert and sync.py behaves
exactly as before (100% backwards compatible).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .io import SyncError, load_yaml_file

# Framework-side config directory holding one <name>.yaml per harness.
HARNESS_CONFIG_DIR = "config/harnesses"

# Environment variable naming the active harness (activation, precedence 2).
HARNESS_ENV_VAR = "AGENT_META_HARNESS"

# Default name of the environment variable overriding a harness's
# checkout-root (override, not activation — activation stays explicit).
DEFAULT_ROOT_ENV = "AGENT_META_HARNESS_ROOT"


@dataclass(frozen=True)
class HarnessConfig:
    """One harness definition parsed from config/harnesses/<name>.yaml.

    Attributes:
        name: Harness identifier; must equal the config file stem.
        checkout_root: Resolved absolute checkout root for this harness.
            All sync write targets must lie inside this directory.
        description: Optional human-readable description.
        branch: Optional branch convention for this harness (e.g.
            ``agent/opencode``) — informational, enforced by convention only.
        default_providers: Optional task-partitioning hint (informational,
            not enforced at runtime — see the RFC follow-ups).
        root_env: Name of the env var that overrides checkout-root.
        source: Path of the YAML file this config was parsed from.
    """

    name: str
    checkout_root: Path
    description: str = ""
    branch: str | None = None
    default_providers: tuple[str, ...] = ()
    root_env: str = DEFAULT_ROOT_ENV
    source: Path | None = None

    def summary(self) -> str:
        """One-line human-readable summary for CLI messages."""
        parts = [f"checkout={self.checkout_root}"]
        if self.branch:
            parts.append(f"branch={self.branch}")
        if self.default_providers:
            parts.append(f"providers={','.join(self.default_providers)}")
        return f"{self.name}: " + ", ".join(parts)


def _resolve_root(raw: str, source_label: str, kind: str) -> Path:
    """Resolve a checkout-root value (``~`` expansion, must be absolute).

    Args:
        raw: Raw path string from the config file or the env override.
        source_label: Where the value came from (for error messages).
        kind: ``"checkout-root"`` or the env var name (for error messages).

    Returns:
        The fully resolved absolute path.

    Raises:
        SyncError: When the value is empty or resolves to a relative path.
    """
    value = (raw or "").strip()
    if not value:
        raise SyncError(f"{source_label}: {kind} must not be empty")
    path = Path(os.path.expanduser(value))
    if not path.is_absolute():
        raise SyncError(
            f"{source_label}: {kind} must be an absolute path (or start with "
            f"'~'), got {value!r}"
        )
    return path.resolve()


def _parse_harness_file(path: Path, env: Mapping[str, str]) -> HarnessConfig:
    """Parse and validate one harness YAML file into a HarnessConfig.

    Raises:
        SyncError: On any schema violation (missing/wrong-typed required
            fields, name/stem mismatch, non-absolute checkout-root).
    """
    data = load_yaml_file(path, on_error="raise")
    block = data.get("harness")
    if not isinstance(block, dict):
        raise SyncError(
            f"Invalid harness config '{path}': expected a 'harness:' mapping "
            f"at the top level, got {type(block).__name__}."
        )
    source_label = f"harness config '{path.name}'"

    name = block.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SyncError(f"{source_label}: 'name' is required and must be a string")
    if name != path.stem:
        raise SyncError(
            f"{source_label}: 'name' ({name!r}) must match the file stem "
            f"({path.stem!r}) — one source of truth for the harness id."
        )

    raw_root = block.get("checkout-root")
    if not isinstance(raw_root, str) or not raw_root.strip():
        raise SyncError(f"{source_label}: 'checkout-root' is required and must be a string")

    root_env = block.get("root-env", DEFAULT_ROOT_ENV)
    if not isinstance(root_env, str) or not root_env.strip():
        raise SyncError(f"{source_label}: 'root-env' must be a non-empty string")
    env_root = (env.get(root_env) or "").strip()
    if env_root:
        checkout_root = _resolve_root(env_root, source_label, f"env override {root_env}")
    else:
        checkout_root = _resolve_root(raw_root, source_label, "checkout-root")

    branch = block.get("branch")
    if branch is not None and (not isinstance(branch, str) or not branch.strip()):
        raise SyncError(f"{source_label}: 'branch' must be a non-empty string when set")

    raw_providers = block.get("default-providers", [])
    if isinstance(raw_providers, str):
        raw_providers = [raw_providers]
    if not isinstance(raw_providers, list) or not all(
        isinstance(p, str) and p.strip() for p in raw_providers
    ):
        raise SyncError(
            f"{source_label}: 'default-providers' must be a list of provider names"
        )

    description = block.get("description", "")
    if not isinstance(description, str):
        description = str(description)

    return HarnessConfig(
        name=name,
        checkout_root=checkout_root,
        description=description,
        branch=branch,
        default_providers=tuple(p.strip() for p in raw_providers),
        root_env=root_env,
        source=path,
    )


def list_harness_names(agent_meta_root: Path) -> list[str]:
    """Return the sorted harness ids available under config/harnesses/.

    Pure directory listing (no YAML parsing), so it stays usable for error
    messages even when a harness file itself is broken.
    """
    hdir = agent_meta_root / HARNESS_CONFIG_DIR
    if not hdir.is_dir():
        return []
    names: set[str] = set()
    for pattern in ("*.yaml", "*.yml"):
        for path in hdir.glob(pattern):
            names.add(path.stem)
    return sorted(names)


def list_harnesses(
    agent_meta_root: Path, env: Mapping[str, str] | None = None
) -> dict[str, HarnessConfig]:
    """Parse every harness config into a {name: HarnessConfig} mapping.

    Raises:
        SyncError: When any harness file violates the schema (fail-closed).
    """
    env = os.environ if env is None else env
    hdir = agent_meta_root / HARNESS_CONFIG_DIR
    if not hdir.is_dir():
        return {}
    result: dict[str, HarnessConfig] = {}
    for pattern in ("*.yaml", "*.yml"):
        for path in sorted(hdir.glob(pattern)):
            harness = _parse_harness_file(path, env)
            result[harness.name] = harness
    return result


def load_harness(
    agent_meta_root: Path, name: str, env: Mapping[str, str] | None = None
) -> HarnessConfig:
    """Load one harness by name from config/harnesses/<name>.yaml.

    Raises:
        SyncError: When the harness does not exist (message lists the
            available names) or its config violates the schema.
    """
    env = os.environ if env is None else env
    available = list_harness_names(agent_meta_root)
    if name not in available:
        listing = ", ".join(available) if available else "(none)"
        raise SyncError(
            f"Unknown harness '{name}' — available harnesses in "
            f"{HARNESS_CONFIG_DIR}/: {listing}"
        )
    for suffix in (".yaml", ".yml"):
        path = agent_meta_root / HARNESS_CONFIG_DIR / f"{name}{suffix}"
        if path.exists():
            return _parse_harness_file(path, env)
    # Unreachable in practice (name came from list_harness_names).
    raise SyncError(f"Harness config file for '{name}' not found in {HARNESS_CONFIG_DIR}/")


def resolve_active_harness(
    agent_meta_root: Path,
    cli_value: str | None = None,
    env: Mapping[str, str] | None = None,
) -> HarnessConfig | None:
    """Resolve the active harness, or None when none is activated.

    Precedence: ``--harness`` CLI flag > ``AGENT_META_HARNESS`` env var.
    Empty/whitespace-only values are treated as unset (direnv-friendly).

    Raises:
        SyncError: When an activated harness is unknown or its config is
            invalid (fail-closed — never silently ignore an activation).
    """
    env = os.environ if env is None else env
    requested = (cli_value or "").strip() or (env.get(HARNESS_ENV_VAR) or "").strip()
    if not requested:
        return None
    return load_harness(agent_meta_root, requested, env)


def is_within(path: Path, root: Path) -> bool:
    """Return True when resolved ``path`` equals or lies under resolved ``root``."""
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def ensure_write_isolation(
    harness: HarnessConfig,
    target: Path,
    log: "SyncLog",  # noqa: F821
    *,
    label: str = "project-root",
    strict: bool = True,
) -> bool:
    """Guard a write target: it must lie inside the harness's checkout root.

    This is the write-isolation choke point for the whole sync: every file
    sync.py writes is under ``project_root`` (or the ``--validate`` test
    repo), so validating those roots validates every individual write path.

    Args:
        harness: The active harness config.
        target: Directory whose contents would be written.
        log: SyncLog for the non-strict warning.
        label: Human-readable target name for messages.
        strict: True → raise SyncError (refuse); False → warn and allow
            (used for the ``--validate`` scratch test repo).

    Returns:
        True when the target is inside the checkout (or warned in
        non-strict mode), False is never returned in strict mode.

    Raises:
        SyncError: In strict mode when the target lies outside the
            harness's declared checkout root.
    """
    target_resolved = Path(target).resolve()
    if is_within(target_resolved, harness.checkout_root):
        return True
    message = _outside_message(harness, target_resolved, label)
    if not strict:
        log.warning(message)
        return False
    raise SyncError(message)


def _outside_message(harness: HarnessConfig, target_resolved: Path, label: str) -> str:
    """Build the refusal/warning message for a target outside the checkout."""
    lines = [
        f"harness '{harness.name}' write isolation violated: {label} "
        f"'{target_resolved}' lies outside the declared checkout root "
        f"'{harness.checkout_root}'",
    ]
    if not harness.checkout_root.exists():
        lines.append(f"  note: checkout root '{harness.checkout_root}' does not exist on this machine")
    lines += [
        f"  source: {harness.source} (override via env {harness.root_env})",
        "  remedy: run sync.py from the checkout this harness is meant to "
        "write into, fix the env override, or drop the harness activation "
        f"(--harness flag / {HARNESS_ENV_VAR})",
    ]
    return "\n".join(lines)
