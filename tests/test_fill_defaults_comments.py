"""Comment-preserving sync auto-fill (issues #1074, #1092).

A plain sync must only materialize the structural fields that are needed at
runtime (``repo_containment`` plus ``project.short`` and the remaining
structural fields) and keep every comment in ``project.yaml``. The seven
preset/flag defaults are written only by ``--fill-defaults`` / ``--init``.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import fill_defaults
from lib.log import SyncLog

TEXT = ("# my header\nproject:\n  name: t\n  prefix: t\n  short: T\n"
        "ai-providers: [Claude]  # inline\nroles:\n- orchestrator\n- developer\n")

SYNC_SKIPPED = (
    "rules-preset:", "speech-mode:", "tier-preset:", "se-focus:",
    "max-parallel-agents:", "debug-mode:", "allow-committed-secrets:",
)


def _cfg(tmp_path):
    p = tmp_path / ".meta-config" / "project.yaml"
    p.parent.mkdir()
    p.write_text(TEXT, encoding="utf-8")
    return p


def test_sync_fill_keeps_comments_and_skips_preset_defaults(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    out = p.read_text(encoding="utf-8")
    assert out.startswith("# my header\nproject:") and "# inline" in out
    assert "repo_containment:" in out
    for key in SYNC_SKIPPED:
        assert key not in out


def test_second_run_is_zero_diff(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    first = p.read_bytes()
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    assert p.read_bytes() == first


def test_explicit_fill_defaults_materializes_presets_and_keeps_comments(tmp_path):
    p = _cfg(tmp_path)
    fill_defaults(p, REPO_ROOT, SyncLog(), False)
    out = p.read_text(encoding="utf-8")
    assert "speech-mode:" in out and "tier-preset:" in out
    assert "# my header" in out and "# inline" in out


def test_sync_fill_adds_derived_project_short_without_losing_header(tmp_path):
    p = tmp_path / ".meta-config" / "project.yaml"
    p.parent.mkdir()
    p.write_text("# my header\nproject:\n  name: t\n  prefix: t\n", encoding="utf-8")
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    out = p.read_text(encoding="utf-8")
    assert out.startswith("# my header\n")
    assert "short: t" in out


def test_crlf_project_yaml_keeps_crlf_on_autofill(tmp_path):
    # PR #1124 advisory 3: the sync write path must read with newline="" --
    # text-mode reading normalises CRLF to LF before the patch is computed.
    p = tmp_path / ".meta-config" / "project.yaml"
    p.parent.mkdir()
    p.write_bytes(TEXT.replace("\n", "\r\n").encode("utf-8"))
    fill_defaults(p, REPO_ROOT, SyncLog(), False, silent=True, materialize_presets=False)
    out = p.read_bytes().decode("utf-8")
    assert "\r\n" in out
    assert "\n" not in out.replace("\r\n", "")
    assert "repo_containment:" in out
    assert "# my header" in out and "# inline" in out


def test_sync_stage_skips_presets_but_init_materializes(monkeypatch, tmp_path):
    import lib.sync_pipeline as sp

    def _capture(init):
        captured = {}

        def fake_fill(config_path, agent_meta_root, log, dry_run, **kwargs):
            captured.update(kwargs)

        monkeypatch.setattr(sp, "fill_defaults", fake_fill)
        monkeypatch.setattr(sp, "load_config", lambda _p: {})
        monkeypatch.setattr(sp, "load_providers_config", lambda *a, **k: {})
        monkeypatch.setattr(sp, "resolve_providers", lambda *a, **k: [])
        monkeypatch.setattr(sp, "resolve_dod_preset_name", lambda *a, **k: "rapid-prototyping")
        monkeypatch.setattr(sp, "resolve_dod", lambda *a, **k: {})
        monkeypatch.setattr(sp, "resolve_rules", lambda *a, **k: {})
        monkeypatch.setattr(sp, "load_platform_config", lambda *a, **k: None)
        args = SimpleNamespace(init=init, dry_run=True)
        sp._sync_stage_config_and_presets(
            REPO_ROOT, tmp_path, tmp_path / "project.yaml", {}, [], args, SyncLog())
        return captured.get("materialize_presets")

    assert _capture(init=False) is False
    assert _capture(init=True) is True
