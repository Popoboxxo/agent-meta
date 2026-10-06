"""Handlebars-style template rendering for agent-context files (partials, conditionals, loops, placeholder variables)."""
from __future__ import annotations
import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..frontmatter import strip_frontmatter
from ..substitution import constant_lookup, substitute_placeholders

if TYPE_CHECKING:
    from ..log import SyncLog

# Permissive placeholder pattern: group 1 captures the name (stripped by the
# lookup below). Excludes block markers ({{#if}}, {{/if}}, {{else}}) and
# partials ({{> name}}) — those are handled by resolve_conditionals(),
# resolve_loops() and resolve_partials().
_PLACEHOLDER_RE = re.compile(r"\{\{([^#>/][^}]*)\}\}")

# Escape syntax {{%VAR%}} -> literal {{VAR}} output, no substitution
# (issue #476 Phase 1 — mirrors scripts/lib/variables.py::substitute()).
# Permissive [^%}]+? (vs. variables.py's uppercase-only [A-Z0-9_]+) because
# context templates may use lowercase placeholder names.
_ESCAPE_RE = re.compile(r"\{\{%\s*([^%}]+?)\s*%\}\}")

# Agent-meta managed block (HTML comment form) shared by the context writers
# and the run-1 fixpoint convergence.
MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)


def substitute_managed_block(text: str, managed_block: str) -> str:
    """Replace the agent-meta managed block in *text* with *managed_block*.

    Makes the FIRST sync of a scaffolded context file converge onto the
    steady-state managed block that every later sync renders (run1 == run2
    fixpoint, AC-4). Function replacement inserts *managed_block* verbatim, so
    backslashes and ``$``-group references are never interpreted (issue #674).

    Returns *text* unchanged when it carries no managed block; creating the
    scaffold itself stays the caller's responsibility.
    """
    if not MANAGED_BLOCK_RE.search(text):
        return text
    return MANAGED_BLOCK_RE.sub(lambda _match: managed_block, text, count=1)


class TemplateBuilder:
    """Handlebars-style template builder with support for partials, conditionals, loops, and variables."""

    def __init__(
        self,
        templates_dir: Path,
        fallback_partials_dir: Path | None = None,
        log: "SyncLog | None" = None,
    ):
        """Initialize the template builder with template and partial directories.

        Args:
            templates_dir: Directory containing .md template files.
            fallback_partials_dir: Optional fallback directory for partials if not found in templates_dir.
            log: Optional SyncLog. When given, resolve_variables() warns on a
                missing (non-PAL_*) placeholder (issue #476 Phase 1) — mirrors
                scripts/lib/variables.py::substitute(). Omitted (default) ->
                no warnings, matching the historic silent-keep behavior.
        """
        self.templates_dir = templates_dir
        self.fallback_partials_dir = fallback_partials_dir
        self._log = log

    def resolve_partials(self, template_str: str) -> str:
        """Resolve {{> partial-name }} inclusions by loading and embedding partial files.

        Args:
            template_str: Template string containing partial references.

        Returns:
            Template string with partials replaced by their content (YAML frontmatter stripped).
        """
        def replace_partial(match):
            partial_name = match.group(1).strip()
            partial_path = self.templates_dir / 'partials' / f"{partial_name}.md"
            if not partial_path.exists() and self.fallback_partials_dir:
                partial_path = self.fallback_partials_dir / f"{partial_name}.md"
            if not partial_path.exists():
                return ""
            # Canonical frontmatter strip (Issue #473) — replaces the former
            # inline content.split('---', 2) duplicate.
            content = strip_frontmatter(partial_path.read_text(encoding='utf-8'))
            return self.resolve_partials(content)
            
        return re.sub(r'\{\{>\s*(.+?)\s*\}\}', replace_partial, template_str)

    def resolve_conditionals(self, template_str: str, variables: dict) -> str:
        """Resolve {{#if variable}}...{{else}}...{{/if}} and {{#unless}} blocks.

        Args:
            template_str: Template string containing conditional blocks.
            variables: Dictionary of variable values for condition evaluation.

        Returns:
            Template string with conditionals replaced based on variable truthiness.
        """
        pattern = r'\{\{#(if|unless)\s+([A-Za-z0-9_]+)\}\}((?:(?!\{\{#(?:if|unless)|\{\{/(?:if|unless)\}\}).)*?)(?:\{\{else\}\}((?:(?!\{\{#(?:if|unless)|\{\{/(?:if|unless)\}\}).)*?))?\{\{/(?:if|unless)\}\}'
        
        def repl(match):
            cond_type = match.group(1)
            var_name = match.group(2)
            if_content = match.group(3)
            else_content = match.group(4) or ""
            
            val = variables.get(var_name)
            is_truthy = bool(val and str(val).lower() != 'false')
            if cond_type == 'unless':
                is_truthy = not is_truthy
                
            if is_truthy:
                return if_content
            return else_content
            
        while re.search(pattern, template_str, re.DOTALL):
            template_str = re.sub(pattern, repl, template_str, flags=re.DOTALL)
        return template_str

    def resolve_loops(self, template_str: str, variables: dict) -> str:
        """Resolve {{#each list}}...{{/each}} loop blocks.

        Args:
            template_str: Template string containing loop blocks.
            variables: Dictionary where values can be lists of objects to iterate over.

        Returns:
            Template string with loops expanded, rendering the inner template for each list item.
        """
        pattern = r'\{\{#each\s+([A-Za-z0-9_]+)\}\}(.*?)\{\{/each\}\}'
        
        def repl(match):
            list_name = match.group(1)
            inner_template = match.group(2)
            
            items = variables.get(list_name, [])
            if not isinstance(items, list):
                items = []
                
            result = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                rendered = inner_template
                for k, v in item.items():
                    # Shared escape-safe core (issue #476): the constant
                    # lookup inserts str(v) verbatim via function
                    # replacement. A raw str replacement would interpret
                    # backslashes as escapes and crash (issue #674).
                    rendered = substitute_placeholders(
                        rendered,
                        r"\{\{\s*(" + re.escape(k) + r")\s*\}\}",
                        constant_lookup(v),
                    )
                result.append(rendered)
            return "".join(result)
            
        while re.search(pattern, template_str, re.DOTALL):
            template_str = re.sub(pattern, repl, template_str, flags=re.DOTALL)
        return template_str
        
    def resolve_variables(self, template_str: str, variables: dict) -> str:
        """Resolve {{variable}} placeholders by substituting values from the variables dictionary.

        Delegates to the shared escape-safe substitution core (issue #476):
        values are injected via function replacement, so backslashes and
        $-group references are never interpreted (issue #674).

        Mirrors scripts/lib/variables.py::substitute()'s three-pass structure
        (issue #476 Phase 1 behavior alignment):
        1. Escaped literals ({{%VAR%}}) are stashed to sentinels so they
           survive the substitution pass untouched.
        2. Real {{VAR}} placeholders are substituted; PAL_* names are exempt
           (never substituted, never warned — handled by the delegation
           syntax engine instead); other missing names warn only if a log
           was given to __init__ (default: silent keep, matching historic
           behavior).
        3. Sentinels are restored as literal {{VAR}} text.

        Args:
            template_str: Template string containing variable references.
            variables: Dictionary of variable names to values.

        Returns:
            Template string with {{variable}} placeholders replaced or left unchanged if not found.
        """
        # Pass 1: protect escaped literals {{%VAR%}} with a unique sentinel.
        _SENTINEL = "\x00ESC\x00"
        escaped: list[str] = []

        def stash_escape(m: re.Match[str]) -> str:
            escaped.append(m.group(1))
            return f"{_SENTINEL}{len(escaped) - 1}{_SENTINEL}"

        template_str = _ESCAPE_RE.sub(stash_escape, template_str)

        # Pass 2: substitute real {{VAR}} placeholders. PAL_* placeholders
        # are handled by the delegation syntax engine, not general
        # substitution — exempt them before the variables-dict lookup.
        def lookup(name: str) -> str | None:
            stripped = name.strip()
            if stripped.startswith("PAL_"):
                return None
            # Whitespace variants ({{ VAR }}) resolve on the stripped name.
            val = variables.get(stripped)
            if val is None:
                return None
            return str(val)

        def keep(matched: str, name: str) -> str:
            stripped = name.strip()
            if stripped.startswith("PAL_"):
                return matched
            if self._log is not None:
                self._log.warn(f"Variable {stripped} not in config — placeholder remains")
            # Unresolved names keep their placeholder form, rebuilt from the
            # stripped name (whitespace variants collapse to {{NAME}}).
            return f"{{{{{stripped}}}}}"

        template_str = substitute_placeholders(template_str, _PLACEHOLDER_RE, lookup, keep)

        # Pass 3: restore escaped literals as {{VAR}} (no substitution happened).
        for i, name in enumerate(escaped):
            template_str = template_str.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

        return template_str

    def build(self, template_name: str, variables: dict) -> str:
        """Load and render a template with the provided variables.

        Processes partials, loops, conditionals, and variable substitutions in order.
        Strips YAML frontmatter (--- ... ---) from templates and partials.

        Args:
            template_name: Name of the template file (without .md extension).
            variables: Dictionary of variable values for rendering.

        Returns:
            Fully rendered template content.

        Raises:
            FileNotFoundError: If the template file is not found.
        """
        template_path = self.templates_dir / f"{template_name}.md"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
            
        content = template_path.read_text(encoding='utf-8')
        # Canonical frontmatter strip (Issue #473) — replaces the former
        # inline content.split('---', 2) duplicate.
        content = strip_frontmatter(content)
                
        content = self.resolve_partials(content)
        content = self.resolve_loops(content, variables)
        content = self.resolve_conditionals(content, variables)
        content = self.resolve_variables(content, variables)
        
        return content
