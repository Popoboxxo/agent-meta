"""Interactive setup wizard for new projects.

Guides the user through creating .meta-config/project.yaml step by step,
then optionally runs --init sync.
"""

import sys
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

try:
    import questionary
    _QUESTIONARY_AVAILABLE = True
except ImportError:
    _QUESTIONARY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ask(prompt: str, default: str = "", validator=None) -> str:
    """Prompt user for input. Returns default if user presses Enter."""
    if _QUESTIONARY_AVAILABLE and sys.stdin.isatty():
        def q_validator(text):
            if not validator: return True
            err = validator(text)
            return err if err else True
        ans = questionary.text(f"  {prompt}", default=default, validate=q_validator).ask()
        if ans is None:
            if default:
                return default
            print("\n  Aborted.")
            sys.exit(0)
        return ans

    if not sys.stdin.isatty():
        return default
    display = f" [{default}]" if default else ""
    while True:
        try:
            raw = input(f"  {prompt}{display}: ").strip()
        except (EOFError, KeyboardInterrupt):
            if default:
                return default
            print("\n  Aborted.")
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
    if _QUESTIONARY_AVAILABLE and sys.stdin.isatty():
        ans = questionary.select(
            f"  {prompt}",
            choices=choices,
            default=default
        ).ask()
        if ans is None:
            if default: return default
            sys.exit(0)
        return ans

    print(f"  {prompt}")
    for i, c in enumerate(choices, 1):
        marker = "*" if c == default else " "
        print(f"    [{i}] {c} {marker}")
    
    default_idx = choices.index(default) + 1 if default in choices else ""
    while True:
        raw = _ask(f"Choose (1-{len(choices)})", default=str(default_idx))
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        if raw.lower() in [c.lower() for c in choices]:
            return next(c for c in choices if c.lower() == raw.lower())
        print(f"  ! Please enter a number between 1 and {len(choices)}.")


def _ask_list(prompt: str, default: list[str], choices: list[str] = None) -> list[str]:
    """Prompt for a comma-separated list. Returns default if empty."""
    if _QUESTIONARY_AVAILABLE and sys.stdin.isatty() and choices is not None:
        # Create questionary choice objects and mark defaults as checked
        q_choices = [questionary.Choice(c, checked=(c in default)) for c in choices]
        ans = questionary.checkbox(
            f"  {prompt}",
            choices=q_choices
        ).ask()
        if ans is None:
            return default
        return ans

    if choices:
        print(f"  {prompt}")
        for i, c in enumerate(choices, 1):
            marker = "*" if c in default else " "
            print(f"    [{i}] {c} {marker}")
        
        default_indices = [str(i+1) for i, c in enumerate(choices) if c in default]
        joined_defaults = ", ".join(default_indices)
        
        while True:
            raw = _ask(f"Choose (comma-separated numbers)", default=joined_defaults)
            parts = [x.strip() for x in raw.split(",") if x.strip()]
            valid = True
            result = []
            for p in parts:
                if p.isdigit():
                    idx = int(p)
                    if 1 <= idx <= len(choices):
                        result.append(choices[idx - 1])
                    else:
                        valid = False
                        break
                else:
                    matching = [c for c in choices if c.lower() == p.lower()]
                    if matching:
                        result.append(matching[0])
                    else:
                        valid = False
                        break
            if valid:
                seen = set()
                return [x for x in result if not (x in seen or seen.add(x))]
            print(f"  ! Invalid input. Please enter numbers (1-{len(choices)}) comma-separated.")
    
    joined = ", ".join(default)
    raw = _ask(f"{prompt} (comma-separated)", default=joined)
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
        return "Prefix must not be empty."
    if len(v) > 8:
        return "Prefix max 8 chars (e.g., 'mp', 'vwf', 'hi')."
    if not v.replace("-", "").isalnum():
        return "Prefix may only contain letters, numbers, and hyphens."
    return None


def _validate_nonempty(v: str) -> str | None:
    return "Must not be empty." if not v else None


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
    if not _QUESTIONARY_AVAILABLE:
        print("  Tip: For arrow key support, install: pip install questionary")
    print("  Abort: Ctrl+C")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Phase 1: Pflichtfelder (Mandatory)
    # ------------------------------------------------------------------
    _section("1. Project Identity")
    print("  INFO: This defines the core identity of your project.")
    name = _ask("Project Name (kebab-case)", default="my-project",
                validator=_validate_nonempty)
    prefix = _ask(
        "Extension Prefix (2-6 chars, e.g., 'mp' for 'my-project')",
        default=name[:3].lower().replace("-", ""),
        validator=_validate_prefix,
    )
    short = _ask("Display Name", default=name)

    _section("2. AI Providers")
    print("  INFO: Select the AI providers you plan to use for your agents.")
    valid_providers = ["Claude", "Gemini", "Continue", "Opencode", "Copilot", "Mammouth"]
    providers_raw = _ask_list("Active AI Providers", default=["Claude"], choices=valid_providers)
    providers = [p for p in providers_raw if p in valid_providers]
    if not providers:
        print("  ! No valid providers selected — using Claude as default.")
        providers = ["Claude"]

    _section("3. Git Configuration")
    print("  INFO: Used by agents to interact with your repository.")
    git_platform = _ask_choice("Git Platform", ["GitHub", "GitLab", "Gitea", "Codeberg"], default="GitHub")
    git_remote = _ask("Remote URL (e.g., https://github.com/owner/repo)", default="")
    git_branch = _ask("Main Branch", default="main")

    # ------------------------------------------------------------------
    # Phase 2: Entscheidung
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  INFO: The following details configure languages, commands, and architecture.")
    do_optional = _ask_choice(
        "Do you want to configure optional details now?\n  (If 'no', defaults will be used. You can ask @agent-meta-manager to do this later!)",
        ["yes", "no"],
        default="no"
    )

    # Standardwerte (Kür-Felder)
    platforms = []
    dod_preset = "standard"
    comm_lang = "English"
    input_lang = "English"
    docs_lang = "English"
    internal_lang = "English"
    code_lang = "English"
    agent_meta_repo = "Popoboxxo/agent-meta"
    project_context = f"{name} — short description."
    project_langs = "TypeScript"
    dev_commands = "bun run build"
    test_commands = "bun test"

    # ------------------------------------------------------------------
    # Phase 3: Optionale Felder (Wenn Ja)
    # ------------------------------------------------------------------
    if do_optional == "yes":
        _section("4. Platform (optional)")
        print("  INFO: Activate platform-specific agent layers (e.g., 'sharkord'). Leave empty if not needed.")
        platform_raw = _ask("Platform(s) — comma-separated or empty", default="")
        platforms = [p.strip() for p in platform_raw.split(",") if p.strip()] if platform_raw else []

        _section("5. Quality Profile (DoD-Preset)")
        print("  INFO: Defines the strictness of the Definition of Done checks.")
        print("  full              — REQ-IDs, tests, CODEBASE_OVERVIEW required")
        print("  standard          — Tests required, REQ-IDs optional")
        print("  rapid-prototyping — All checks disabled for fast iteration")
        dod_preset = _ask_choice("DoD-Preset", ["full", "standard", "rapid-prototyping"], default="standard")

        _section("6. Languages")
        print("  INFO: Define the languages used by agents for different types of communication.")
        comm_lang = _ask("Agent→User Language (COMMUNICATION_LANGUAGE)", default="English")
        input_lang = _ask("User→Agent Language (USER_INPUT_LANGUAGE)", default="English")
        docs_lang = _ask("External Docs Language (DOCS_LANGUAGE)", default="English")
        internal_lang = _ask(
            "Internal Docs Language (INTERNAL_DOCS_LANGUAGE)",
            default="English",
        )
        code_lang = _ask("Code/Commit Language (CODE_LANGUAGE)", default="English")

        _section("7. Project Variables")
        print("  INFO: Technical context and commands for the agents.")
        agent_meta_repo = _ask("agent-meta GitHub Repo (owner/repo)", default="Popoboxxo/agent-meta")
        project_context = _ask("Short Project Description (PROJECT_CONTEXT)", default=f"{name} — short description.")
        project_langs = _ask("Programming Languages (PROJECT_LANGUAGES)", default="TypeScript")
        dev_commands = _ask("Build/Dev Command (DEV_COMMANDS)", default="bun run build")
        test_commands = _ask("Test Command (TEST_COMMANDS)", default="bun test")

    # ------------------------------------------------------------------
    # Assemble config
    # ------------------------------------------------------------------
    config: dict = {
        "agent-meta-version": _read_version(agent_meta_root),
        "ai-providers": providers,
        "roles": [
            "orchestrator",
            "agent-meta-manager",
            "developer",
            "documenter",
            "meta-feedback",
            "log-analyzer",
            "git"
        ]
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
        "PROJECT_GOAL": f"Primary goal of {name}.",
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
        "CODE_CONVENTIONS": "- TypeScript ES6+, no `any`, no `var`",
        "ARCHITECTURE": "src/\\n  index.ts  # Entry-Point",
        "REQ_CATEGORIES": "- Core features\\n- Non-functional requirements",
    }

    # ------------------------------------------------------------------
    # Preview + write
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Configuration — Preview")
    print("=" * 60)
    _print_config_summary(config)

    if dry_run:
        print("\n  DRY-RUN — no files will be written.")
        return config

    if target_config.exists():
        overwrite = _ask_choice(
            f"\n  {target_config} already exists. Overwrite?",
            ["yes", "no"],
            default="no",
        )
        if overwrite.lower() != "yes":
            print("  Aborted — keeping existing config.")
            sys.exit(0)

    target_config.parent.mkdir(parents=True, exist_ok=True)
    _write_config(target_config, config)
    print(f"\n  ✓ Config written: {target_config}")
    
    print("\n  " + "=" * 60)
    print("  TIP: Now use @agent-meta-manager to activate more agents")
    print("       and fine-tune your project settings!")
    print("  " + "=" * 60 + "\n")

    return config


def _read_version(agent_meta_root: Path) -> str:
    version_file = agent_meta_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _print_config_summary(config: dict) -> None:
    proj = config.get("project", {})
    vars_ = config.get("variables", {})
    print(f"  Project:    {proj.get('name')}  [prefix: {proj.get('prefix')}]")
    print(f"  Providers:  {', '.join(config.get('ai-providers', []))}")
    print(f"  Platform:   {', '.join(config.get('platforms', [])) or '(none)'}")
    print(f"  DoD-Preset: {config.get('dod-preset', 'standard')}")
    print(f"  Language:   {vars_.get('COMMUNICATION_LANGUAGE')} / {vars_.get('DOCS_LANGUAGE')}")
    print(f"  Git:        {vars_.get('GIT_PLATFORM')} — {vars_.get('GIT_REMOTE_URL') or '(not set)'}")


def _write_config(path: Path, config: dict) -> None:
    """Write config as YAML with a short header comment."""
    if not _YAML_AVAILABLE:
        print(
            "ERROR: PyYAML not installed but required for --setup wizard. "
            "Run: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)
    header = (
        "# agent-meta project.yaml — generated by --setup wizard\n"
        "# Edit this file to customize variables and settings.\n"
        "# Then run: py .agent-meta/scripts/sync.py\n\n"
    )
    body = yaml.dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(header + body, encoding="utf-8")
