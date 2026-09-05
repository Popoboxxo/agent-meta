"""Provider Abstraction Layer — Bootstrap Engine.

Führt provider-spezifische Bootstrap-Aktionen nach Agent-Generierung aus:
- Gemini: Erzeugt define_subagent Instruktionen
- ZCode: Injiziert statische Roster-Registrierungs-Instruktionen
- Continue: Erzeugt Config-Update Instruktionen

Usage:
    from scripts.lib.bootstrap import BootstrapEngine
    engine = BootstrapEngine()
    result = engine.run_bootstrap(provider="Gemini", agents_dir=Path("..."))
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class BootstrapEngine:
    """Handles provider-specific agent registration bootstrap."""

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dir = config_dir
        self._bootstrap_registry: dict[str, Any] | None = None

    @property
    def bootstrap_registry(self) -> dict[str, Any]:
        if self._bootstrap_registry is None:
            path = self.config_dir / "provider-bootstrap.yaml"
            try:
                with open(path, encoding="utf-8") as f:
                    if yaml is not None:
                        self._bootstrap_registry = yaml.safe_load(f)
                    else:
                        self._bootstrap_registry = {}
            except (FileNotFoundError, yaml.YAMLError):
                self._bootstrap_registry = {}
        return self._bootstrap_registry or {}

    def get_bootstrap_config(self, provider: str) -> dict[str, Any]:
        """Return bootstrap configuration for a provider."""
        return self.bootstrap_registry.get("bootstrap", {}).get(provider, {})

    def run_bootstrap(
        self,
        provider: str,
        agents_dir: Path,
        project_root: Path | None = None,
        *,
        dry_run: bool = False,
        log: Any = None,
        context_file: str | None = None,
        compact: bool = False,
        agents_label: str | None = None,
    ) -> dict[str, Any]:
        """Execute provider-specific bootstrap actions.

        The extra keyword-only args (dry_run/log/context_file/compact/
        agents_label) only matter for the api-based mechanism (Gemini's
        GEMINI.md injection) — config-based bootstrap (Continue) ignores
        them, it has no dry-run gate or compact mode of its own.

        Returns a dict with results/instructions.
        """
        config = self.get_bootstrap_config(provider)
        mechanism = config.get("mechanism", "none")

        if mechanism == "none" or config.get("action") == "none":
            return {"status": "skipped", "reason": f"{provider} needs no bootstrap"}

        if mechanism == "api-based":
            return self._bootstrap_api_based(
                provider, agents_dir, config, project_root,
                dry_run=dry_run, log=log, context_file=context_file,
                compact=compact, agents_label=agents_label,
            )
        elif mechanism == "config-based":
            return self._bootstrap_config_based(provider, agents_dir, config, project_root)

        return {"status": "skipped", "reason": f"Unknown mechanism: {mechanism}"}

    def _bootstrap_api_based(
        self,
        provider: str,
        agents_dir: Path,
        config: dict[str, Any],
        project_root: Path | None,
        *,
        dry_run: bool = False,
        log: Any = None,
        context_file: str | None = None,
        compact: bool = False,
        agents_label: str | None = None,
    ) -> dict[str, Any]:
        """Inject session-start bootstrap instructions into the provider's
        context file (e.g. GEMINI.md or the provider's AGENTS.md) for
        api-based providers (Gemini, ZCode).

        Issue #628: moved here from provider_transform.py's bespoke
        _inject_gemini_bootstrap so agent_sync.py has one unified bootstrap
        call site (like Continue's config-based path already had) instead of
        a special-cased direct call. Only handles the
        "inject-bootstrap-instructions" action.

        Instruction sources, selected via the provider-bootstrap.yaml entry:
        - ``instructions_mode: static`` + non-empty ``instructions``: the
          registry's static text is injected verbatim (trailing newlines
          stripped) — no per-agent roster generation (no agents_dir.glob).
          Used by ZCode, whose harness has no define_subagent API.
        - default (no ``instructions_mode``, i.e. Gemini): the per-agent
          roster is generated from ``agents_dir`` via
          generate_gemini_bootstrap_instructions().
        """
        if config.get("action") != "inject-bootstrap-instructions":
            return {"status": "skipped", "reason": f"unsupported action for {provider}: {config.get('action')}"}

        if project_root is None:
            return {"status": "error", "reason": "project_root required for api-based bootstrap"}

        static_instructions = config.get("instructions")
        if config.get("instructions_mode") == "static" and static_instructions:
            # Static mode (e.g. ZCode): inject the registry text verbatim —
            # the generated-per-agent path (agents_dir.glob) is skipped.
            instructions = static_instructions.rstrip("\n")
        else:
            instructions = self.generate_gemini_bootstrap_instructions(
                agents_dir, compact=compact, agents_label=agents_label or agents_dir.name
            )
            if not instructions:
                return {"status": "skipped", "reason": "no agents found"}

        context_file = context_file or ".gemini/GEMINI.md"
        # Path-traversal guard: context_file must resolve inside project_root.
        resolved = (project_root / context_file).resolve()
        root_resolved = project_root.resolve()
        if root_resolved not in resolved.parents and resolved != root_resolved:
            if log:
                log.warning(f"{context_file} path escapes project root — skipping bootstrap injection")
            return {"status": "error", "reason": "context_file escapes project_root"}

        target_path = project_root / context_file
        if not target_path.exists():
            if log:
                log.warning(f"{target_path.relative_to(project_root)!s} does not exist — cannot inject bootstrap instructions")
            return {"status": "skipped", "reason": f"{context_file} does not exist"}

        existing = target_path.read_text(encoding="utf-8")
        marker_begin = "<!-- agent-meta:bootstrap-begin -->"
        marker_end = "<!-- agent-meta:bootstrap-end -->"
        block = f"{marker_begin}\n{instructions}\n{marker_end}"

        if marker_begin in existing:
            pattern = re.compile(re.escape(marker_begin) + ".*?" + re.escape(marker_end), re.DOTALL)
            new_content = pattern.sub(block, existing, count=1)
        else:
            new_content = existing.rstrip("\n") + "\n\n" + block + "\n"

        if new_content == existing:
            if log:
                log.skip(str(target_path.relative_to(project_root)), "bootstrap instructions unchanged")
            return {"status": "skipped", "mechanism": "api-based", "reason": "bootstrap instructions unchanged"}

        if log:
            log.action("UPDATE", str(target_path.relative_to(project_root)), "bootstrap instructions")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")

        return {"status": "success", "provider": provider, "mechanism": "api-based", "instructions": instructions}

    def _bootstrap_config_based(
        self,
        provider: str,
        agents_dir: Path,
        config: dict[str, Any],
        project_root: Path | None,
    ) -> dict[str, Any]:
        """Update Continue config.yaml with agent entries."""
        agents = sorted(agents_dir.glob("*.md"))

        if project_root is None:
            return {
                "status": "error",
                "reason": "project_root required for config-based bootstrap",
            }

        config_path = project_root / ".continue" / "config.yaml"
        if not config_path.exists():
            return {
                "status": "skipped",
                "reason": f"{config_path} does not exist",
            }

        existing = config_path.read_text(encoding="utf-8")

        marker = "# agent-meta:managed-agents-begin"
        marker_end = "# agent-meta:managed-agents-end"
        agent_entries = "".join(f"  - name: {f.stem}\n    prompt: prompts/{f.name}\n" for f in agents)
        managed_block = (
            f"{marker}\n"
            "# Auto-generated by agent-meta sync.py — do not edit manually\n"
            f"agents:\n{agent_entries}{marker_end}"
        )

        if marker in existing:
            pattern = re.compile(
                re.escape(marker) + ".*?" + re.escape(marker_end),
                re.DOTALL,
            )
            new_content = pattern.sub(managed_block, existing, count=1)
        else:
            new_content = existing.rstrip("\n") + "\n\n" + managed_block + "\n"

        if new_content != existing:
            config_path.write_text(new_content, encoding="utf-8")
            return {
                "status": "success",
                "provider": provider,
                "mechanism": "config-updated",
                "agent_count": len(agents),
                "instructions": f"{len(agents)} Agenten in .continue/config.yaml eingetragen.",
            }

        return {
            "status": "skipped",
            "mechanism": "config-based",
            "reason": "config.yaml already up to date",
        }

    def generate_gemini_bootstrap_instructions(
        self, agents_dir: Path, compact: bool = False,
        agents_label: str = ".gemini/agents",
    ) -> str:
        """Generate human-readable bootstrap instructions for Gemini GEMINI.md injection.

        compact=True (issue #540 B6) replaces the explicit per-agent enumeration
        (~106 of ~124 lines; discoverable via ``ls <agents_label>``) with a short
        form. The instruction core — session-start obligation, define_subagent
        registration and the runtime warning — is preserved in both modes.
        """
        agents = sorted(agents_dir.glob("*.md"))
        if not agents:
            return ""

        if compact:
            return "\n".join(
                [
                    "",
                    "## Agent Bootstrap — Session-Start Pflicht",
                    "",
                    "Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.",
                    f"Lies alle `.md`-Dateien in `{agents_label}` und registriere jeden Agenten "
                    "unter seinem Dateinamen (ohne `.md`) via `define_subagent`.",
                    "Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.).",
                    "",
                    "> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**",
                    "> und der Orchestrator kann nicht delegieren.",
                ]
            )

        lines = [
            "",
            "## Agent Bootstrap — Session-Start Pflicht",
            "",
            "Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session.",
            "**Führe folgende Schritte zu Beginn JEDER Session aus:**",
            "",
            "1. Lies alle Agenten-Dateien aus `.gemini/agents/`:",
        ]

        for agent_file in agents:
            lines.append(f"   - `{agent_file.name}` → registriere als `{agent_file.stem}`")

        lines.extend(
            [
                "",
                "2. Registriere jeden Agenten via define_subagent API-Call:",
                "   ```",
            ]
        )

        for agent_file in agents:
            lines.append(f'   define_subagent(name="{agent_file.stem}", ...)')

        lines.extend(
            [
                "   ```",
                "",
                "3. Erst danach: Bearbeite User-Anfragen (Delegation an Orchestrator etc.)",
                "",
                "> **Ohne diese Registrierung existieren die Agenten NICHT in der Runtime**",
                "> und der Orchestrator kann nicht delegieren.",
            ]
        )

        return "\n".join(lines)
