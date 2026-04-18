"""Interactive setup wizard for new projects.

Guides the user through creating .meta-config/project.yaml step by step,
then optionally runs --init sync.
"""

import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ask(prompt: str, default: str = "", validator=None) -> str:
    """Prompt user for input. Returns default if user presses Enter."""
    display = f" [{default}]" if default else ""
    while True:
        try:
            raw = input(f"  {prompt}{display}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Abgebrochen.")
            sys.exit(0)
        value = raw if raw else default
        if validator:
            error = validator(value)
            if error:
                print(f"  ! {error}")
                continue
        return value


def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
    """Prompt for a choice from a list."""
    options = "/".join(
        c.upper() if c == default else c for c in choices
    )
    while True:
        raw = _ask(f"{prompt} ({options})", default=default)
        if raw.lower() in [c.lower() for c in choices]:
            return next(c for c in choices if c.lower() == raw.lower())
        print(f"  ! Gültige Optionen: {', '.join(choices)}")


def _ask_list(prompt: str, default: list[str]) -> list[str]:
    """Prompt for a comma-separated list. Returns default if empty."""
    joined = ", ".join(default)
    raw = _ask(f"{prompt} (kommagetrennt)", default=joined)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_prefix(v: str) -> str | None:
    if not v:
        return "Prefix darf nicht leer sein."
    if len(v) > 8:
        return "Prefix maximal 8 Zeichen (z.B. 'mp', 'vwf', 'hi')."
    if not v.replace("-", "").isalnum():
        return "Prefix darf nur Buchstaben, Zahlen und Bindestriche enthalten."
    return None


def _validate_nonempty(v: str) -> str | None:
    return "Darf nicht leer sein." if not v else None


# ---------------------------------------------------------------------------
# Wizard
# ---------------------------------------------------------------------------

def run_setup_wizard(
    agent_meta_root: Path,
    project_root: Path,
    target_config: Path,
    dry_run: bool,
) -> dict:
    """Run the interactive setup wizard and return the generated config dict."""

    print("\n" + "=" * 60)
    print("  agent-meta Setup-Wizard")
    print("  Drücke Enter um den vorgeschlagenen Wert zu übernehmen.")
    print("  Abbruch: Strg+C")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Projekt-Identität
    # ------------------------------------------------------------------
    _section("1/7  Projekt-Identität")
    name = _ask("Projektname (kebab-case)", default="mein-projekt",
                validator=_validate_nonempty)
    prefix = _ask(
        "Prefix (2–6 Zeichen, Kürzel für Extension-Dateien, z.B. 'mp')",
        default=name[:3].lower().replace("-", ""),
        validator=_validate_prefix,
    )
    short = _ask("Kurzname (Anzeigename)", default=name)

    # ------------------------------------------------------------------
    # 2. AI-Provider
    # ------------------------------------------------------------------
    _section("2/7  AI-Provider")
    print("  Unterstützte Provider: Claude, Gemini, Continue")
    providers_raw = _ask_list("Aktive Provider", default=["Claude"])
    valid_providers = {"Claude", "Gemini", "Continue"}
    providers = [p for p in providers_raw if p in valid_providers]
    if not providers:
        print("  ! Keine gültigen Provider — verwende Claude als Default.")
        providers = ["Claude"]

    # ------------------------------------------------------------------
    # 3. Plattform
    # ------------------------------------------------------------------
    _section("3/7  Plattform (optional)")
    print("  Platform-Layer aktivieren z.B. 'sharkord' für Sharkord-Plugin-Projekte.")
    print("  Leer lassen wenn kein plattformspezifischer Agent-Layer benötigt wird.")
    platform_raw = _ask("Plattform(en) — kommagetrennt oder leer lassen", default="")
    platforms = [p.strip() for p in platform_raw.split(",") if p.strip()] if platform_raw else []

    # ------------------------------------------------------------------
    # 4. DoD-Preset
    # ------------------------------------------------------------------
    _section("4/7  Qualitätsprofil (DoD-Preset)")
    print("  full              — REQ-IDs, Tests, CODEBASE_OVERVIEW (strengstes Profil)")
    print("  standard          — Tests ja, REQ-IDs nein")
    print("  rapid-prototyping — Alle Checks deaktiviert (schnellstes Prototyping)")
    dod_preset = _ask_choice("DoD-Preset", ["full", "standard", "rapid-prototyping"], default="standard")

    # ------------------------------------------------------------------
    # 5. Sprache
    # ------------------------------------------------------------------
    _section("5/7  Sprache")
    comm_lang = _ask("Sprache Agent→Nutzer (COMMUNICATION_LANGUAGE)", default="Deutsch")
    input_lang = _ask("Sprache Nutzer→Agent (USER_INPUT_LANGUAGE)", default="Deutsch")
    docs_lang = _ask("Externe Doku-Sprache — README, Issues (DOCS_LANGUAGE)", default="Englisch")
    internal_lang = _ask(
        "Interne Doku-Sprache — REQUIREMENTS, ARCHITECTURE (INTERNAL_DOCS_LANGUAGE)",
        default="Deutsch",
    )
    code_lang = _ask("Code-Sprache — Kommentare, Commits (CODE_LANGUAGE)", default="Englisch")

    # ------------------------------------------------------------------
    # 6. Git
    # ------------------------------------------------------------------
    _section("6/7  Git-Konfiguration")
    git_platform = _ask_choice("Git-Plattform", ["GitHub", "GitLab", "Gitea"], default="GitHub")
    git_remote = _ask("Remote-URL (z.B. https://github.com/owner/repo)", default="")
    git_branch = _ask("Haupt-Branch", default="main")
    agent_meta_repo = _ask(
        "agent-meta GitHub-Repo für Feedback-Issues (owner/repo)",
        default="Popoboxxo/agent-meta",
    )

    # ------------------------------------------------------------------
    # 7. Schlüssel-Variablen
    # ------------------------------------------------------------------
    _section("7/7  Projekt-Variablen")
    project_context = _ask(
        "Kurze Projektbeschreibung (PROJECT_CONTEXT)",
        default=f"{name} — kurze Beschreibung.",
    )
    project_langs = _ask("Programmiersprachen (PROJECT_LANGUAGES)", default="TypeScript")
    dev_commands = _ask("Build-/Dev-Kommando (DEV_COMMANDS)", default="bun run build")
    test_commands = _ask("Test-Kommando (TEST_COMMANDS)", default="bun test")

    # ------------------------------------------------------------------
    # Assemble config
    # ------------------------------------------------------------------
    config: dict = {
        "agent-meta-version": _read_version(agent_meta_root),
        "ai-providers": providers,
    }
    if platforms:
        config["platforms"] = platforms

    config["dod-preset"] = dod_preset
    config["project"] = {
        "name": name,
        "prefix": prefix,
        "short": short,
    }
    config["variables"] = {
        "PROJECT_CONTEXT": project_context,
        "PROJECT_GOAL": f"Primäres Ziel von {name}.",
        "PROJECT_LANGUAGES": project_langs,
        "COMMUNICATION_LANGUAGE": comm_lang,
        "USER_INPUT_LANGUAGE": input_lang,
        "DOCS_LANGUAGE": docs_lang,
        "INTERNAL_DOCS_LANGUAGE": internal_lang,
        "CODE_LANGUAGE": code_lang,
        "AGENT_META_REPO": agent_meta_repo,
        "GIT_PLATFORM": git_platform,
        "GIT_REMOTE_URL": git_remote,
        "GIT_MAIN_BRANCH": git_branch,
        "DEV_COMMANDS": dev_commands,
        "TEST_COMMANDS": test_commands,
        "BUILD_COMMANDS": dev_commands,
        "CODE_CONVENTIONS": "- TypeScript ES6+, kein `any`, kein `var`",
        "ARCHITECTURE": "src/\n  index.ts  # Entry-Point",
        "REQ_CATEGORIES": "- Kernfunktionalität\n- Nichtfunktionale Anforderungen",
    }

    # ------------------------------------------------------------------
    # Preview + write
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Konfiguration — Vorschau")
    print("=" * 60)
    _print_config_summary(config)

    if dry_run:
        print("\n  DRY-RUN — keine Dateien werden geschrieben.")
        return config

    if target_config.exists():
        overwrite = _ask_choice(
            f"\n  {target_config} existiert bereits. Überschreiben?",
            ["ja", "nein"],
            default="nein",
        )
        if overwrite.lower() != "ja":
            print("  Abgebrochen — bestehende Config wird behalten.")
            sys.exit(0)

    target_config.parent.mkdir(parents=True, exist_ok=True)
    _write_config(target_config, config)
    print(f"\n  ✓ Config geschrieben: {target_config}")

    return config


def _read_version(agent_meta_root: Path) -> str:
    version_file = agent_meta_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _print_config_summary(config: dict) -> None:
    proj = config.get("project", {})
    vars_ = config.get("variables", {})
    print(f"  Projekt:    {proj.get('name')}  [prefix: {proj.get('prefix')}]")
    print(f"  Provider:   {', '.join(config.get('ai-providers', []))}")
    print(f"  Plattform:  {', '.join(config.get('platforms', [])) or '(keine)'}")
    print(f"  DoD-Preset: {config.get('dod-preset', 'standard')}")
    print(f"  Sprache:    {vars_.get('COMMUNICATION_LANGUAGE')} / {vars_.get('DOCS_LANGUAGE')}")
    print(f"  Git:        {vars_.get('GIT_PLATFORM')} — {vars_.get('GIT_REMOTE_URL') or '(nicht gesetzt)'}")


def _write_config(path: Path, config: dict) -> None:
    """Write config as YAML with a short header comment."""
    header = (
        "# agent-meta project.yaml — generiert von --setup wizard\n"
        "# Bearbeite diese Datei um weitere Variablen zu ergänzen.\n"
        "# Danach: py .agent-meta/scripts/sync.py\n\n"
    )
    body = yaml.dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(header + body, encoding="utf-8")
