from __future__ import annotations
import re
from pathlib import Path


class TemplateBuilder:
    """Handlebars-style template builder with support for partials, conditionals, loops, and variables."""

    def __init__(self, templates_dir: Path, fallback_partials_dir: Path | None = None):
        """Initialize the template builder with template and partial directories.

        Args:
            templates_dir: Directory containing .md template files.
            fallback_partials_dir: Optional fallback directory for partials if not found in templates_dir.
        """
        self.templates_dir = templates_dir
        self.fallback_partials_dir = fallback_partials_dir

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
            content = partial_path.read_text(encoding='utf-8')
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].lstrip()
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
                    # Function replacement: re.sub treats the return value
                    # literally. A raw str replacement would interpret
                    # backslashes as escapes and crash (issue #674).
                    rendered = re.sub(r'\{\{\s*' + re.escape(k) + r'\s*\}\}', lambda m, val=str(v): val, rendered)
                result.append(rendered)
            return "".join(result)
            
        while re.search(pattern, template_str, re.DOTALL):
            template_str = re.sub(pattern, repl, template_str, flags=re.DOTALL)
        return template_str
        
    def resolve_variables(self, template_str: str, variables: dict) -> str:
        """Resolve {{variable}} placeholders by substituting values from the variables dictionary.

        Args:
            template_str: Template string containing variable references.
            variables: Dictionary of variable names to values.

        Returns:
            Template string with {{variable}} placeholders replaced or left unchanged if not found.
        """
        def repl(match):
            var_name = match.group(1).strip()
            val = variables.get(var_name)
            if val is not None:
                return str(val)
            return f"{{{{{var_name}}}}}"
            
        return re.sub(r'\{\{([^#>/][^}]*)\}\}', repl, template_str)

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
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].lstrip()
                
        content = self.resolve_partials(content)
        content = self.resolve_loops(content, variables)
        content = self.resolve_conditionals(content, variables)
        content = self.resolve_variables(content, variables)
        
        return content
