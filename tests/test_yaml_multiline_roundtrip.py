"""Regression test for issue #717: a project.yaml multi-line variable value
(e.g. SYSTEM_DEPENDENCIES with several `\n`-joined list items) must survive
a full YAML re-dump round-trip byte-for-line, not fold onto one line."""
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml

from lib.io import yaml_dump_preserving_multiline


def test_single_newline_separated_items_survive_a_redump():
    # Before the fix: PyYAML's default emitter represents this as a
    # single-quoted/folded scalar -- a single embedded \n folds to a space on
    # reparse, silently merging "- A" and "- B" onto one line.
    data = {"variables": {"SYSTEM_DEPENDENCIES": "- Python: `>=3.8`\n- bun: `>=1.0.0`"}}

    dumped = yaml_dump_preserving_multiline(yaml, data, allow_unicode=True,
                                            default_flow_style=False, sort_keys=False)
    reloaded = yaml.safe_load(dumped)

    assert reloaded["variables"]["SYSTEM_DEPENDENCIES"] == data["variables"]["SYSTEM_DEPENDENCIES"]
    assert "|" in dumped  # forced literal-block style, human-diffable


def test_single_line_string_is_unaffected():
    data = {"variables": {"SYSTEM_URLS": ""}}
    dumped = yaml_dump_preserving_multiline(yaml, data, allow_unicode=True,
                                            default_flow_style=False, sort_keys=False)
    assert yaml.safe_load(dumped) == data


def test_stream_argument_writes_in_place_like_yaml_dump():
    data = {"a": "line1\nline2"}
    buf = io.StringIO()
    result = yaml_dump_preserving_multiline(yaml, data, buf, allow_unicode=True,
                                            default_flow_style=False, sort_keys=False)
    assert result is None
    assert yaml.safe_load(buf.getvalue()) == data


def test_config_full_rewrite_preserves_multiline_variable(tmp_path):
    # Integration: config.py's actual full-file rewrite path
    # (_write_yaml_with_comments, triggered by fill_defaults()) must not
    # regress a pre-existing multi-line value when it adds an unrelated
    # missing default field.
    from lib.config import fill_defaults
    from lib.log import SyncLog

    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: demo\n  prefix: dm\n  short: demo\n"
        "ai-providers:\n  - Claude\n"
        "variables:\n  SYSTEM_DEPENDENCIES: |\n    - A\n    - B\n",
        encoding="utf-8",
    )
    log = SyncLog()
    fill_defaults(config_path, REPO_ROOT, log, dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    # The input `|` literal block clips to a single trailing newline on parse
    # (YAML clip semantics), so the round-trip-stable value is "- A\n- B\n" --
    # the #717 bug being guarded is the single embedded \n FOLDING to a space,
    # which would yield "- A - B\n". The embedded newline must survive.
    assert reloaded["variables"]["SYSTEM_DEPENDENCIES"] == "- A\n- B\n"
    assert "\n- B" in reloaded["variables"]["SYSTEM_DEPENDENCIES"]  # not folded to a space
