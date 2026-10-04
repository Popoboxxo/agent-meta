"""Repo-wide pytest configuration.

Warning-only guard: pytest's basetemp must not live inside the repository.

Why (2026-09-19/20 disk incident): a basetemp under ``<repo>/.tmp/`` makes
``tmp_path`` part of the repo. Two consequences:

1. Any test that copies the repo can copy its own output back into itself and
   grow without bound (16 GB / 432,138 entries observed on 2026-09-20).
2. Tests that probe repo-root discovery (``.meta-config/`` lookup, containment
   root checks) find the real repo instead of an isolated fixture.

The guard deliberately only *warns* — it never calls ``pytest.exit`` or
``pytest.fail``. Running the suite with an in-repo basetemp stays allowed,
because that run is a legitimate diagnostic for disk safety.

See ``docs/concepts/repo-containment-prison-mode.md`` §5.5.
"""

import os
import tempfile
from pathlib import Path

from pytest import PytestWarning

_AGENT_META_ROOT = Path(__file__).resolve().parents[1]

_EXTERNAL_BASETEMP_HINT = "--basetemp=/tmp/$USER/pytest-agent-meta"


def _is_within(path, root):
    """Python 3.8-compatible stand-in for ``Path.is_relative_to`` (3.9+)."""
    path = Path(path).resolve()
    root = Path(root).resolve()
    return path == root or root in path.parents


def effective_basetemp(config):
    """Best-effort basetemp pytest will use, derived from CLI/env only.

    ``--basetemp`` wins. Otherwise pytest falls back to the system temp dir
    (``TMPDIR``, else ``tempfile.gettempdir()``) as the basetemp *root*.
    """
    given = getattr(config.option, "basetemp", None)
    if given:
        return Path(given)
    return Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


def basetemp_inside_repo(config):
    """True when the effective basetemp lives inside the repository root."""
    return _is_within(effective_basetemp(config), _AGENT_META_ROOT)


def pytest_configure(config):
    """Warn (never fail) when the effective basetemp is inside the repo."""
    if not basetemp_inside_repo(config):
        return
    config.issue_config_time_warning(
        PytestWarning(
            f"pytest basetemp '{effective_basetemp(config)}' is inside the "
            f"repository ({_AGENT_META_ROOT}). tmp_path then becomes part of the "
            "repo, so repo-root-discovery tests can find the real .meta-config/ "
            "and any repo copy can recurse into its own output. Pass an external "
            f"basetemp, e.g. {_EXTERNAL_BASETEMP_HINT}. Warning only — the run "
            "continues."
        ),
        stacklevel=2,
    )
