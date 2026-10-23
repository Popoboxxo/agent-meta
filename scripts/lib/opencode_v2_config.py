"""Managed-merge engine for the opencode v2 config surface.

The decision layer is pure: ``merge_managed_path`` decides *what* a managed path
should become without touching a file or a log, which keeps the decision table
testable row by row in ``tests/test_opencode_v2_config.py``.
``sync_opencode_v2_managed_keys`` (spec §3.2, Task 9) is the I/O layer around
it: it reads ``opencode.json`` + the state file, renders the decisions and
writes through the shared ``isolation`` helpers and ``io.write_checked`` (no
new I/O variant). Ownership (``owns_opencode_surface``) is decided before any
state is read, so non-owner providers are strict no-ops (N-M2, AC-B20).

The table itself is ``SPEC-OPENCODE-V2-SUPPORT-2026-10-22`` §3.2: for one
managed dotted ``path`` ``P`` with target value ``T`` (``target is None`` =
"no longer managed"), current file value ``C`` (``ABSENT`` = the key does not
exist) and state entry ``S[P]``:

| row | condition | action | state afterwards |
|---|---|---|---|
| 1 | ``T``, ``C == ABSENT``, ``P not in S`` | write | ``value=T``, prior ABSENT |
| 2 | ``T``, ``P in S``, ``C == S.value``, ``C != T`` | write | ``value=T``, prior kept |
| 3 | ``T``, ``P not in S``, ``C`` exists, ``C != T`` | keep + WARN | no entry (user value) |
| 3a | ``T``, ``P not in S``, ``C == T`` | noop | ``value=T``, ``prior=T`` |
| 3b | ``T``, ``P in S``, ``C != S.value`` | keep + WARN | unchanged |
| 3c | ``T``, ``P in S``, ``C == ABSENT`` | keep + WARN | unchanged |
| 4 | ``T == None``, ``P in S``, ``C == S.value`` | remove | entry dropped |
| 4a | ``T == None``, ``P in S``, ``C != S.value`` | keep + WARN | entry dropped |
| — | ``T``, ``P in S``, ``C == S.value == T`` | noop | unchanged |

State encoding (single form of this spec): ``{"value": <json>, "prior":
<json|null>, "prior_absent": <bool>}``. ``prior_absent: true`` means the key
did not exist before the first write — ``prior`` is then ``null`` and carries no
meaning. A legitimate JSON ``null`` prior is ``prior: null`` with
``prior_absent: false`` and is restored as ``null`` by row 4; the two cases must
stay distinguishable because ``null`` is a valid value.

Amendment B1 (2026-10-23): the engine is generic over dotted paths. No
auxiliary title-model path is managed here — the C0 spike could not verify such
a target, so it was dropped from the spec; callers must not assume one exists.

Amendment B2 (2026-10-23): this module is the **single owner** of
``experimental.subagent_depth``. The initial settings transform
(``context.apply_settings_surface_shape``) only removes the dead top-level
``subagent_depth``; the depth is written exclusively through this engine, so
rows 1/3a/2/4 apply as specified and a project override or a v2→v1 rollback
behaves (spec Amendment B2).

Task 8 (B.5) adds the data predicates (``v2_active``,
``owns_opencode_surface``), the shared ``opencode_state_path``, the project
option reader, the managed key set (spec §3.3) and the structural
``find_plaintext_secrets`` check (spec §3.3/AC-B10). Activation and ownership
are decided on resolved values only — no provider name, no ``surface-version``
comparison.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import io, isolation, providers
from .dispatch_depth import required_depth_int
from .log import SyncLog

# Resolved v2 values (spec §3.1). Activation is a pure function of these two
# resolved values — never of the raw ``surface-version`` selector or a provider
# name. Providers declare them through the registry maps (Task 6).
V2_FRONTMATTER_MECHANISM = "opencode-native-v2"
V2_MCP_FORMAT = "opencode-json-v2"

# Valid secret indirection (spec §3.3): a value of this exact shape refers to an
# environment variable and is never a plaintext secret.
_ENV_PLACEHOLDER_RE = re.compile(r"^\{env:[A-Za-z_][A-Za-z0-9_]*\}$")

# Project options that only exist on a v2 surface (spec §3.1/AC-B13). On a
# non-v2 surface they are ignored, not silently dropped: the writer warns per
# configured key. Keep this the single source — ``small-model`` was removed by
# Amendment B1 and must not reappear here. A tuple keeps the warning order
# deterministic.
_V2_ONLY_OPTION_KEYS = (
    "experimental-subagent-depth",
    "experimental-todo",
    "providers",
    "model-variants",
    "cli",
)

# A plaintext finding is decided by the KEY NAME, never by the value pattern
# (AC-B10/AC-T7): only keys that name a credential are inspected.
_SECRET_NAME_MARKERS = ("key", "secret", "token")

# State namespaces (spec §3.2) — re-exported from ``isolation``, which owns the
# state file, so the literals have exactly one source of truth. Each writer
# reads/writes only its own namespace (IC-09, no clobbering).
STATE_KEYS_KEY = isolation._STATE_V2_KEYS
STATE_PERMISSIONS_KEY = isolation._STATE_V2_PERMISSIONS
STATE_CLI_KEY = isolation._STATE_V2_CLI
STATE_MCP_KEY = isolation._STATE_V2_MCP


class _Absent:
    """Sentinel: the JSON key does not exist.

    Distinct from ``None`` on purpose — ``null`` is a legitimate JSON value, so
    "missing" and "present but null" must not collapse into one representation.
    Always compare with ``is``; the sentinel is never serialized.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "ABSENT"


ABSENT = _Absent()


@dataclass(frozen=True)
class MergeResult:
    """Decision for one managed path.

    ``action`` is one of ``"write"`` (set the path to ``value``), ``"remove"``
    (delete the path when ``value is ABSENT``, else restore ``value``),
    ``"keep"`` (leave the file alone) or ``"noop"`` (nothing to do at all).
    ``value`` is the value the path should end up with — the target value for
    a write, the restored prior / ``ABSENT`` for a removal, and the observed
    file value for a keep/noop. ``state`` is the new state entry, ``None`` when
    the path is no longer tracked; ``warning`` carries the user-facing warning
    text when a user value was preserved.
    """

    action: str
    value: object
    state: dict | None
    warning: str | None


def _warning(path: str) -> str:
    """The canonical warning text for a preserved user value (spec §3.2)."""
    return f"opencode-v2-managed: {path} user value kept"


def _state_entry(value: object, prior: object, prior_absent: bool) -> dict:
    """Build a state entry in the encoded form (``ABSENT`` never leaks out).

    Passing the ``ABSENT`` sentinel as ``prior`` is accepted and encoded as
    ``prior: null`` + ``prior_absent: true`` — the sentinel itself is never
    stored, so every state entry stays JSON-serializable.
    """
    if prior is ABSENT:
        prior_absent = True
    return {
        "value": value,
        "prior": None if prior_absent else prior,
        "prior_absent": prior_absent,
    }


def _normalise_entry(entry: object) -> dict | None:
    """Normalise a stored state entry, or ``None`` when the path is untracked.

    Missing/foreign state degrades to "untracked" rather than raising. A dict
    without ``prior_absent`` is read with the older ``{value, prior}``
    semantics of spec A (``prior is None`` = key was absent), so a partially
    written entry can never be mistaken for "a null prior existed".
    """
    if not isinstance(entry, dict) or "value" not in entry:
        return None
    prior_absent = entry.get("prior_absent")
    if not isinstance(prior_absent, bool):
        prior_absent = entry.get("prior") is None
    return {
        "value": entry["value"],
        "prior": entry.get("prior"),
        "prior_absent": prior_absent,
    }


def _same(left: object, right: object) -> bool:
    """JSON-value equality that keeps ``true``/``1`` and ``3``/``3.0`` apart.

    Plain ``==`` would equate booleans with numbers (Python semantics), which
    would let a user's ``1`` look like agent-meta's ``true`` and turn a "user
    changed the value" case into a silent overwrite. Recursive so the same
    holds for nested objects such as ``providers.<id>``.
    """
    if left is ABSENT or right is ABSENT:
        return left is right
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        return all(_same(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def _merge_removal(path: str, current: object, state: dict | None) -> MergeResult:
    """Rows 4/4a: the path is no longer managed."""
    if state is None:
        return MergeResult(action="noop", value=current, state=None, warning=None)
    if current is ABSENT or not _same(current, state["value"]):
        # 4a — the file no longer holds what agent-meta wrote: the user's
        # decision wins, management just ends (no restore, no overwrite).
        return MergeResult(action="keep", value=current, state=None, warning=_warning(path))
    if state["prior_absent"]:
        # 4 — the key was absent before the first write: delete it again.
        return MergeResult(action="remove", value=ABSENT, state=None, warning=None)
    return MergeResult(action="remove", value=state["prior"], state=None, warning=None)


def merge_managed_path(
    path: str,
    target: object | None,
    current: object,
    entry: dict | None,
) -> MergeResult:
    """Decide the merge for one managed path (spec §3.2 decision table).

    ``path`` is the dotted JSON path, used only for the warning text.
    ``target`` is the value agent-meta wants, or ``None`` when the path is no
    longer managed (removal). ``current`` is the value read from the file, or
    ``ABSENT`` when the key does not exist. ``entry`` is this path's state
    entry, or ``None`` when agent-meta never wrote it.
    """
    state = _normalise_entry(entry)

    if target is None:
        return _merge_removal(path, current, state)

    if state is None:
        if current is ABSENT:
            # Row 1 — nothing there yet: write and remember that it was absent.
            return MergeResult(
                action="write",
                value=target,
                state=_state_entry(target, ABSENT, prior_absent=True),
                warning=None,
            )
        if _same(current, target):
            # Row 3a — the user already has the target value: adopt it without
            # writing, and record it as its own prior so a rollback keeps it.
            return MergeResult(
                action="noop",
                value=current,
                state=_state_entry(target, target, prior_absent=False),
                warning=None,
            )
        # Row 3 — an unmanaged user value differs: never overwrite it.
        return MergeResult(
            action="keep", value=current, state=None, warning=_warning(path)
        )

    if current is ABSENT or not _same(current, state["value"]):
        # Rows 3c/3b — the user deleted or changed our value since the last
        # write. Respect that (no re-write) and keep tracking the deviation.
        return MergeResult(
            action="keep", value=current, state=state, warning=_warning(path)
        )

    if _same(current, target):
        # Idempotency — the file already holds the current target value.
        return MergeResult(action="noop", value=current, state=state, warning=None)

    # Row 2 — the file holds exactly what agent-meta wrote: update it, keeping
    # the original prior so a later rollback still restores the user's value.
    return MergeResult(
        action="write",
        value=target,
        state=_state_entry(target, state["prior"], state["prior_absent"]),
        warning=None,
    )


# ---------------------------------------------------------------------------
# Activation and provider/file ownership (spec §3.2, N-M2)
# ---------------------------------------------------------------------------

def _provider_entry(provider_config: dict, provider: str) -> dict:
    """Return the entry for *provider* from a registry **or** a single entry.

    Mirrors ``isolation._opencode_runtime_gate_entries``: callers pass either
    the full resolved registry (``{provider: {...}}``) or the already-resolved
    per-provider entry. Anything unusable degrades to ``{}`` instead of raising.
    """
    if not isinstance(provider_config, dict):
        return {}
    entry = provider_config.get(provider)
    if isinstance(entry, dict):
        return entry
    return provider_config


def _mcp_config(provider_config: dict) -> dict:
    """The ``mcp-config`` block of a single provider entry, else ``{}``."""
    if not isinstance(provider_config, dict):
        return {}
    mcp_config = provider_config.get("mcp-config")
    return mcp_config if isinstance(mcp_config, dict) else {}


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def v2_active(provider_config: dict, provider: str) -> bool:
    """True iff the **resolved** entry carries both v2 values (spec §3.1).

    Purely data-driven: ``frontmatter-mechanism == "opencode-native-v2"`` AND
    ``mcp-config.format == "opencode-json-v2"``. The raw ``surface-version``
    selector and the provider name are never inspected.
    """
    pc = _provider_entry(provider_config, provider)
    agent_transform = pc.get("agent-transform")
    mcp_config = pc.get("mcp-config")
    return (
        isinstance(agent_transform, dict)
        and agent_transform.get("frontmatter-mechanism") == V2_FRONTMATTER_MECHANISM
        and isinstance(mcp_config, dict)
        and mcp_config.get("format") == V2_MCP_FORMAT
    )


def owns_opencode_surface(provider_config: dict, provider: str) -> bool:
    """True iff this provider owns the managed opencode file (spec §3.2, N-M2).

    Ownership requires a *selectable* v2 JSON surface in the registry entry
    (``mcp-config.surface-formats`` is a non-empty dict containing
    ``"opencode-json-v2"``) **and** a non-empty ``mcp-config.committed-file``.
    Non-owners (Claude, Gemini, Mammouth, ...) never write or roll back here,
    regardless of any existing state entries. Pure data check — no provider
    literal, no ``surface-version`` comparison.
    """
    mcp_config = _mcp_config(_provider_entry(provider_config, provider))
    surface_formats = mcp_config.get("surface-formats")
    if not isinstance(surface_formats, dict) or not surface_formats:
        return False
    if V2_MCP_FORMAT not in surface_formats.values():
        return False
    return _non_empty_string(mcp_config.get("committed-file"))


def _owned_committed_file(provider_config: dict) -> str | None:
    """The owner's ``committed-file``, accepting a single entry or a registry.

    A single entry answers directly. For a registry, the surface owner is
    located deterministically via the same marker ``owns_opencode_surface``
    uses (``surface-formats`` containing the v2 format) — never by provider
    name and never by a hardcoded filename.
    """
    mcp_config = _mcp_config(provider_config)
    committed = mcp_config.get("committed-file")
    if _non_empty_string(committed):
        return committed
    if isinstance(provider_config, dict):
        for entry in provider_config.values():
            if not isinstance(entry, dict):
                continue
            entry_mcp = _mcp_config(entry)
            surface_formats = entry_mcp.get("surface-formats")
            if (
                isinstance(surface_formats, dict)
                and V2_MCP_FORMAT in surface_formats.values()
            ):
                candidate = entry_mcp.get("committed-file")
                if _non_empty_string(candidate):
                    return candidate
    return None


def opencode_state_path(project_root: Path, provider_config: dict) -> Path:
    """The state file of the owner: ``<committed-file dir>/.opencode/...``.

    Single source for every writer and rollback of this spec (spec §3.2/§3.5/
    §3.8). Derived from the provider's resolved ``mcp-config.committed-file``,
    so ``opencode.json`` yields exactly ``isolation._OPENCODE_STATE_FILE``
    without hardcoding the filename here. No file I/O.
    """
    base = Path(project_root)
    committed = _owned_committed_file(provider_config)
    if committed is not None:
        base = base / Path(committed).parent
    return base / isolation._OPENCODE_STATE_FILE


# ---------------------------------------------------------------------------
# Project options and the managed key set (spec §3.1/§3.3)
# ---------------------------------------------------------------------------

def project_options(config: dict, provider: str) -> dict:
    """The ``provider-options.<provider>`` block, or ``{}``.

    The provider is a parameter so no provider name literal is needed; unset,
    non-dict or malformed values degrade to ``{}`` (schema validation owns the
    hard errors).
    """
    if not isinstance(config, dict):
        return {}
    options = config.get("provider-options")
    if not isinstance(options, dict):
        return {}
    value = options.get(provider)
    return value if isinstance(value, dict) else {}


def warn_ignored_v2_options(
    config: dict,
    provider: str,
    provider_config: dict,
    log: SyncLog,
) -> None:
    """Warn about project options that only a v2 surface understands (AC-B13).

    A non-v2 surface ignores every key of :data:`_V2_ONLY_OPTION_KEYS`; the
    warning makes that visible instead of dropping the configuration silently
    (spec §3.1 error paths). On v2 nothing is ignored and nothing is logged.
    The keys are read from ``provider-options.<provider>`` only — no provider
    name literal and no ``surface-version`` comparison.
    """
    if v2_active(provider_config, provider):
        return
    options = project_options(config, provider)
    for key in _V2_ONLY_OPTION_KEYS:
        if key in options:
            log.warning(
                f"opencode-v2-option-ignored: {key} requires surface-version v2"
            )


def _positive_int(value: object) -> bool:
    """JSON-schema ``integer, minimum 1`` — ``True``/``False`` are not ints."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def build_managed_keys(
    config: dict,
    provider: str,
    provider_config: dict,
    agent_meta_root: Path,
    log: SyncLog | None = None,
) -> dict[str, object]:
    """Return the v2 managed key set as ``{dotted path: value}`` (spec §3.3).

    Empty when the surface is not v2-active. Otherwise:

    - ``experimental.subagent_depth`` from the project option, else the
      provider capability's ``required_depth`` — omitted when neither exists;
    - ``experimental.todo`` only when the project explicitly sets it (``False``
      is a set value and is written as such);
    - ``providers.<id>`` per project entry, the whole object as a passthrough
      of the documented inner shape (``settings.baseURL``, ``env``, ...). The
      writer never interprets or validates that shape.

    A ``providers.<id>`` entry whose value is ``None`` is skipped with a
    warning: in ``{path: value}`` a ``None`` target means "no longer managed"
    (row 4), so passing it through would turn a malformed project value into a
    removal of an existing managed block (QA-B-11).

    ``$schema`` is deliberately absent (v2 has no published schema; AC-B11), and
    Amendment B1 removed ``agents.title.model`` entirely (Q6 UNVERIFIED) — no
    title/small-model path is produced here.
    """
    if not v2_active(provider_config, provider):
        return {}

    options = project_options(config, provider)
    managed: dict[str, object] = {}

    depth = options.get("experimental-subagent-depth")
    if not _positive_int(depth):
        try:
            capabilities = providers.load_provider_capabilities(agent_meta_root)
        except Exception:  # noqa: BLE001 - unreadable registry -> omit depth
            capabilities = {}
        caps = capabilities.get(provider) if isinstance(capabilities, dict) else None
        depth = required_depth_int(caps)
    if depth is not None:
        managed["experimental.subagent_depth"] = depth

    todo = options.get("experimental-todo")
    if isinstance(todo, bool):
        managed["experimental.todo"] = todo

    provider_entries = options.get("providers")
    if isinstance(provider_entries, dict):
        for provider_id, entry in provider_entries.items():
            if entry is None:
                if log is not None:
                    log.warning(
                        f"opencode-v2-provider-skipped: providers.{provider_id} is null"
                    )
                continue
            managed[f"providers.{provider_id}"] = entry

    return managed


# ---------------------------------------------------------------------------
# Structural secret check (spec §3.3, AC-B10/AC-T7)
# ---------------------------------------------------------------------------

def _is_secret_name(key: object) -> bool:
    lowered = str(key).lower()
    return any(marker in lowered for marker in _SECRET_NAME_MARKERS)


def _is_env_placeholder(value: object) -> bool:
    return isinstance(value, str) and _ENV_PLACEHOLDER_RE.match(value) is not None


def _walk_plaintext_secrets(obj: object, path: str, secret_context: bool) -> list[str]:
    findings: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else str(key)
            # A secret-named key taints its whole subtree: an object value such
            # as ``{"token": {"value": "PLAINTEXT"}}`` is still a plaintext
            # secret, so the context is propagated to the children.
            child_secret = secret_context or _is_secret_name(key)
            findings.extend(
                _walk_plaintext_secrets(value, child_path, child_secret)
            )
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            findings.extend(
                _walk_plaintext_secrets(value, f"{path}[{index}]", secret_context)
            )
    elif secret_context and not _is_env_placeholder(obj):
        findings.append(path)
    return findings


def find_plaintext_secrets(obj: object, path: str) -> list[str]:
    """Return the paths of plaintext credentials under *path* (spec §3.3).

    A value is a finding iff its **key name** contains ``key``, ``secret`` or
    ``token`` (case-insensitive) and the value is not a valid ``{env:VAR}``
    placeholder. Nested objects and lists are walked (``oauth`` structures
    included); list elements are addressed as ``path[index]``. Decisions are
    name-based on purpose — the concrete value is never matched against a
    secret pattern (AC-B10: the test must not bind to the value).
    """
    return _walk_plaintext_secrets(obj, path, secret_context=False)


# ---------------------------------------------------------------------------
# Dotted-path helpers for the file layer
#
# Managed paths are dotted JSON paths (``experimental.todo``,
# ``providers.<id>``). The helpers below work on a freshly parsed document and
# never serialize the ``ABSENT`` sentinel. Container pruning after a removal is
# generic: every ancestor that became an empty object is dropped, so
# ``experimental`` disappears on a full v2→v1 rollback and a hypothetical
# ``agents.title``/``agents`` chain would be pruned the same way (Amendment B1:
# no title path is managed, so that branch is simply never exercised).
# ---------------------------------------------------------------------------

def _get_path(document: dict, path: str) -> object:
    """Return the value at dotted *path*, or the ``ABSENT`` sentinel."""
    node: object = document
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return ABSENT
        node = node[part]
    return node


def _set_path(document: dict, path: str, value: object) -> bool:
    """Create missing parent objects and set the leaf at dotted *path*.

    Returns ``False`` (and leaves the document untouched) when an ancestor
    exists but is not an object: a scalar/array under a container name is user
    data, and replacing it to reach a managed leaf would silently destroy it
    (QA-B-03). The caller then keeps the document and warns instead.
    """
    parts = path.split(".")
    # Validate every *existing* ancestor before mutating anything, so a failure
    # never leaves a half-created branch behind.
    node: object = document
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            break
        node = node[part]
        if not isinstance(node, dict):
            return False
    node = document
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    return True


def _prune_empty_parents(document: dict, parts: list[str]) -> None:
    """Drop ancestors of *parts* that became empty objects after a removal.

    Walks upwards from the immediate parent: as soon as an ancestor still has
    content (or is not an object) the chain is left alone. This is deliberately
    path-generic — no container name is special-cased.
    """
    for depth in range(len(parts) - 1, 0, -1):
        ancestor = _get_path(document, ".".join(parts[:depth]))
        if not isinstance(ancestor, dict) or ancestor:
            return
        if depth == 1:
            document.pop(parts[0], None)
        else:
            parent = _get_path(document, ".".join(parts[: depth - 1]))
            if isinstance(parent, dict):
                parent.pop(parts[depth - 1], None)


def _delete_path(document: dict, path: str) -> None:
    """Delete the key at dotted *path* and prune now-empty parent containers."""
    parts = path.split(".")
    node = document
    for part in parts[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            return
        node = child
    node.pop(parts[-1], None)
    _prune_empty_parents(document, parts)


def _plaintext_secret_paths(targets: dict[str, object]) -> list[str]:
    """Structural check of the ``providers`` subtree that is about to be written.

    Runs on the managed values themselves (not on a value pattern) and therefore
    also in dry-run, where ``write_checked`` skips its own scan (spec §3.3 m-7).
    The path prefix is passed through verbatim, so a finding reads
    ``providers.x.headers.X-Api-Key``.
    """
    findings: list[str] = []
    for path in sorted(targets):
        if path == "providers" or path.startswith("providers."):
            findings.extend(find_plaintext_secrets(targets[path], path))
    return findings


def sync_opencode_v2_managed_keys(
    project_root: Path,
    config: dict,
    provider: str,
    provider_config: dict,
    agent_meta_root: Path,
    log: SyncLog,
    dry_run: bool,
    *,
    claimed_files: set[str],
) -> None:
    """Merge the v2 managed keys into the EXISTING ``opencode.json`` (spec §3.2).

    The ownership guard is the first statement: a provider that does not own the
    managed surface (no selectable v2 JSON surface / no ``committed-file``) never
    reads state, writes a file or logs — regardless of any state entries left by
    an earlier sync (AC-B20, N-M2). Only the owner derives the target file and
    the state path from its own resolved data (``committed-file`` and
    ``opencode_state_path``); nothing is hardcoded.

    Every managed path is decided by :func:`merge_managed_path` over the
    union of the state entries and the current targets, which is exactly the
    rollback path: on v1 the target set is empty, so rows 4/4a restore the prior
    value or delete the key and prune empty parents. ``keep``/``noop`` leave the
    file untouched (a user value is never overwritten, a no-op never rewrites or
    reformats the file), and the state namespace is rewritten only when it
    actually changed. A parse error or a structural secret finding returns
    without writing anything (data-loss protection, rule 6; AC-B10/AC-T7).
    The regex-based secret gate is delegated to ``io.write_checked`` with the
    same parameters as ``mcp_provider_config._write_json_config`` (spec §3.3);
    for the committed file ``verify_gitignored`` is ``False`` (that flag is only
    set for the local/secrets file, #586).

    ``claimed_files`` is the caller's run-scoped claim registry (N-M2 (3)) and
    is a required keyword argument (QA-B-04): the first owner of a managed file
    with actual work acts, every further claimant logs
    ``opencode-v2-owner-conflict: <file>`` and returns without touching file or
    state. The claim is taken only after the "nothing to do" determination
    (QA-B-02): an owner with neither targets nor state must not shadow the next
    claimant, otherwise ``[A, B]`` and ``[B, A]`` would diverge. It is passed in
    — never module-level — so no state leaks between sync runs and both orders
    end in the same file/state (AC-B20).
    """
    if not owns_opencode_surface(provider_config, provider):
        return

    pc = _provider_entry(provider_config, provider)
    committed = _mcp_config(pc).get("committed-file")
    if not _non_empty_string(committed):
        # Unreachable behind the ownership guard; keeps the type contract local
        # (no hardcoded filename on any path).
        return

    root = Path(project_root)
    # Route the derived state path through ``safe_path`` exactly like the
    # managed file below (QA-B-05): a ``committed-file`` with ``..`` must not be
    # able to move the state file outside the project root.
    state_path = isolation.safe_path(
        root, opencode_state_path(root, pc).relative_to(root)
    )
    state = isolation._read_state(state_path, STATE_KEYS_KEY)
    targets = build_managed_keys(config, provider, pc, agent_meta_root, log)

    # No-op without an active v2 surface AND without prior management: a v1
    # project that never had v2 keys must stay byte-identical (AC-B2/B7).
    if not targets and not state:
        # AC-B13: an "ignored option" warning is not file work and must not be
        # lost to this early return (a non-v2 surface never produces targets).
        warn_ignored_v2_options(config, provider, provider_config, log)
        return

    # Claim after the no-work check and before the managed file is read
    # (QA-B-02): a claimant with nothing to do never blocks the real owner.
    if committed in claimed_files:
        log.warning(f"opencode-v2-owner-conflict: {committed}")
        return
    claimed_files.add(committed)

    warn_ignored_v2_options(config, provider, provider_config, log)

    secret_findings = _plaintext_secret_paths(targets)
    if secret_findings:
        for finding in secret_findings:
            log.error(committed, f"opencode-v2-secret-plaintext: {finding}")
        return

    file_path = isolation.safe_path(root, committed)
    existing = isolation._read_json_safe(file_path, log)
    if existing is None:
        if file_path.exists():
            return  # parse error — warning already emitted, never overwrite it
        existing = {}
    elif not isinstance(existing, dict):
        return  # a non-object document is not ours to rewrite (data-loss guard)

    new_state: dict[str, dict] = {}
    changed = False
    for path in sorted(set(state) | set(targets)):
        result = merge_managed_path(
            path,
            targets.get(path),
            _get_path(existing, path),
            state.get(path),
        )
        if result.warning:
            log.warning(result.warning)
        if result.action == "write":
            if not _set_path(existing, path, result.value):
                # A non-object ancestor is user data: keep it and warn instead
                # of clobbering it, and do not record state we never wrote.
                log.warning(_warning(path))
                continue
            changed = True
        elif result.action == "remove":
            if result.value is ABSENT:
                _delete_path(existing, path)
            elif not _set_path(existing, path, result.value):
                log.warning(_warning(path))
                continue
            changed = True
        # ``keep`` / ``noop``: the file is left exactly as it is.
        if result.state is not None:
            new_state[path] = result.state

    if changed:
        content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        written = io.write_checked(
            file_path,
            content,
            log,
            committed,
            allow_secrets=(config or {}).get("allow-committed-secrets", False),
            verify_gitignored=False,
            config=config,
            dry_run=dry_run,
        )
        if written:
            log.action("WRITE", committed, "opencode-v2 managed keys")
        else:
            log.skip(committed, "opencode-v2 managed keys unchanged")
    else:
        log.skip(committed, "opencode-v2 managed keys unchanged")

    if new_state != state:
        isolation._write_state(state_path, new_state, dry_run, STATE_KEYS_KEY)
