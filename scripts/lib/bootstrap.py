"""Provider Abstraction Layer — Bootstrap Engine.

Führt provider-spezifische Bootstrap-Aktionen nach Agent-Generierung aus:
- Gemini: Erzeugt define_subagent Instruktionen
- Continue: Erzeugt Config-Update Instruktionen

Usage:
    from scripts.lib.bootstrap import BootstrapEngine
    engine = BootstrapEngine()
    result = engine.run_bootstrap(provider="Gemini", agents_dir=Path("..."))
"""

import json
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
            with open(path) as f:
                if yaml is not None:
                    self._bootstrap_registry = yaml.safe_load(f)
                else:
                    self._bootstrap_registry = {}
        return self._bootstrap_registry or {}

    def get_bootstrap_config(self, provider: str) -> dict[str, Any]:
        """Return bootstrap configuration for a provider."""
        return self.bootstrap_registry.get("bootstrap", {}).get(provider, {})

    def run_bootstrap(
        self, provider: str, agents_dir: Path, project_root: Path | None = None
    ) -> dict[str, Any]:
        """Execute provider-specific bootstrap actions.

        Returns a dict with results/instructions.
        """
        config = self.get_bootstrap_config(provider)
        mechanism = config.get("mechanism", "none")

        if mechanism == "none" or config.get("action") == "none":
            return {"status": "skipped", "reason": f"{provider} needs no bootstrap"}

        if mechanism == "api-based":
            return self._bootstrap_api_based(provider, agents_dir, config, project_root)
        elif mechanism == "config-based":
            return self._bootstrap_config_based(provider, agents_dir, config, project_root)

        return {"status": "skipped", "reason": f"Unknown mechanism: {mechanism}"}

    def _bootstrap_api_based(
        self,
        provider: str,
        agents_dir: Path,
        config: dict[str, Any],
        project_root: Path | None,
    ) -> dict[str, Any]:
        """Generate define_subagent instructions for API-based providers (Gemini)."""
        agents = sorted(agents_dir.glob("*.md"))
        instructions: list[dict[str, str]] = []

        for agent_file in agents:
            name = agent_file.stem
            content = agent_file.read_text()

            description = self._extract_description(content)

            instructions.append(
                {
                    "agent": name,
                    "define_call": (
                        f'define_subagent(name="{name}", '
                        f'description="{description}", '
                        f'system_prompt="<content of {name}.md>")'
                    ),
                }
            )

        return {
            "status": "success",
            "provider": provider,
            "mechanism": "api-define_subagent",
            "agent_count": len(instructions),
            "instructions": instructions,
            "summary": (
                f"Bei Session-Beginn {len(instructions)} Agenten "
                "via define_subagent registrieren."
            ),
        }

    def _bootstrap_config_based(
        self,
        provider: str,
        agents_dir: Path,
        config: dict[str, Any],
        project_root: Path | None,
    ) -> dict[str, Any]:
        """Generate config update instructions for config-based providers (Continue)."""
        agents = sorted(agents_dir.glob("*.md"))
        return {
            "status": "success",
            "provider": provider,
            "mechanism": "config-based",
            "agent_count": len(agents),
            "instructions": (
                f"Trage {len(agents)} Agenten in .continue/config.yaml ein."
            ),
        }

    def _extract_description(self, content: str) -> str:
        """Extract agent description from frontmatter or fallback."""
        for line in content.splitlines():
            if line.startswith("description:"):
                return line.split(":", 1)[1].strip().strip('"')
        return "No description available"

    def generate_gemini_bootstrap_instructions(self, agents_dir: Path) -> str:
        """Generate human-readable bootstrap instructions for Gemini GEMINI.md injection."""
        agents = sorted(agents_dir.glob("*.md"))
        if not agents:
            return ""

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
