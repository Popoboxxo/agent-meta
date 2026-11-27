"""Doku-Konsistenz Commands-System (AC-1.1, AC-3.2-3.4, OF-4).

Prüft Guide, Setup-Doku und Requirements gegen Code/Config.
`knowledge/` wird bewusst nicht geprüft.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "guides" / "features" / "commands.md"
INSTANTIATE = ROOT / "docs" / "guides" / "setup" / "instantiate-project.md"
REQS = ROOT / "docs" / "REQUIREMENTS.md"
BARE_INDEX = ".agent-meta-managed"


PARTIAL = ROOT / "templates" / "context" / "partials" / "commands-section.md"
LAYER_RE = re.compile(r"commands/[0-2]-\w+/")


def _commands_indexes() -> set:
    data = yaml.safe_load((ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    values = set()

    def walk(node):
        if isinstance(node, dict):
            for key, val in node.items():
                if key == "commands_managed_index" and val:
                    values.add(val)
                walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    assert values, "kein commands_managed_index in ai-providers.yaml"
    return values


def test_guide_names_commands_index_without_contradiction():
    text = GUIDE.read_text(encoding="utf-8")
    for index in _commands_indexes():
        assert index in text, f"Guide nennt {index} nicht"
        # Intent: every line mentioning the bare role index must also name the
        # Continue commands index, otherwise the doc contradicts the config.
        offenders = [
            line.strip()
            for line in text.splitlines()
            if BARE_INDEX in line and index not in line
        ]
        assert not offenders, f"Zeile nennt Basis-Index ohne Continue-Index: {offenders}"


def test_guide_command_list_matches_generic_commands():
    actual = {p.stem for p in (ROOT / "commands" / "1-generic").glob("*.md")}
    text = GUIDE.read_text(encoding="utf-8")
    heading = "## Verfügbare Framework-Commands"
    assert heading in text, f"Überschrift fehlt im Guide: {heading}"
    section = text.split(heading, 1)[1]
    section = re.split(r"\n---\n", section, maxsplit=1)[0]
    listed = re.findall(r"^\|\s*`/project:([\w-]+)`", section, flags=re.M)
    assert len(listed) == len(set(listed)), "Duplikate in Command-Liste"
    assert set(listed) == actual, (
        f"fehlend: {sorted(actual - set(listed))}, überzählig: {sorted(set(listed) - actual)}"
    )


def test_guide_layer_description_matches_partial():
    text = GUIDE.read_text(encoding="utf-8")
    partial_layers = set(LAYER_RE.findall(PARTIAL.read_text(encoding="utf-8")))
    assert partial_layers, "Partial nennt keine Schichtpfade"
    heading = "## Schichten-Modell"
    assert heading in text, f"Überschrift fehlt im Guide: {heading}"
    section = re.split(r"\n---\n", text.split(heading, 1)[1], maxsplit=1)[0]
    table_rows = [ln for ln in section.splitlines() if ln.startswith("|")]
    guide_layers = {m for ln in table_rows for m in LAYER_RE.findall(ln)}
    assert guide_layers == partial_layers, (
        f"Guide {sorted(guide_layers)} != Partial {sorted(partial_layers)}"
    )
    collision = text.split("**Namenskollision:**", 1)
    assert len(collision) == 2, "Kollisions-Abschnitt fehlt im Guide"
    assert "ohne Backup" in collision[1].split("\n\n", 1)[0]
    assert not re.search(r"\|\s*Prio(rit[äa]t)?\s*(\||$)", section, re.I), "Prio-Spalte vorhanden"
    assert "← 3-project" not in text


def test_instantiate_project_has_no_wrong_project_commands_path():
    for path in (INSTANTIATE, GUIDE):
        text = path.read_text(encoding="utf-8")
        assert "3-project/commands" not in text, f"{path.name} nennt 3-project/commands"


def test_requirements_cmd_03_06_consistent_with_config_index():
    indexes = _commands_indexes()
    rows_all = {
        m.group(1): m.group(0)
        for m in re.finditer(r"^\| (REQ-CMD-0[368]) \|.*$", REQS.read_text(encoding="utf-8"), re.M)
    }
    rows = {k: v for k, v in rows_all.items() if k != "REQ-CMD-08"}
    assert set(rows) == {"REQ-CMD-03", "REQ-CMD-06"}
    assert "REQ-CMD-08" in rows_all
    for index in indexes:
        assert index in rows["REQ-CMD-03"]
    for row in rows.values():
        stripped = row
        for index in indexes:
            stripped = stripped.replace(index, "")
        # Bare index is only allowed as explicit contrast ("Rollen-Index `...`").
        stripped = stripped.replace(f"Rollen-Index `{BARE_INDEX}`", "")
        assert BARE_INDEX not in stripped, f"Zeile nennt Basis-Index ohne Config-Index: {row}"
    assert "Kollision" in rows_all["REQ-CMD-08"], "REQ-CMD-08 nennt Kollision nicht"
