import re
from pathlib import Path

class TemplateBuilder:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def resolve_partials(self, template_str: str) -> str:
        def replace_partial(match):
            partial_name = match.group(1).strip()
            partial_path = self.templates_dir / 'partials' / f"{partial_name}.md"
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
        pattern = r'\{\{#if\s+([A-Za-z0-9_]+)\}\}(.*?)(?:\{\{else\}\}(.*?))?\{\{/if\}\}'
        
        def repl(match):
            var_name = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3) or ""
            
            val = variables.get(var_name)
            if val and str(val).lower() != 'false':
                return if_content
            return else_content
            
        while re.search(pattern, template_str, re.DOTALL):
            template_str = re.sub(pattern, repl, template_str, flags=re.DOTALL)
        return template_str

    def resolve_loops(self, template_str: str, variables: dict) -> str:
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
                    rendered = re.sub(r'\{\{\s*' + re.escape(k) + r'\s*\}\}', str(v), rendered)
                result.append(rendered)
            return "".join(result)
            
        while re.search(pattern, template_str, re.DOTALL):
            template_str = re.sub(pattern, repl, template_str, flags=re.DOTALL)
        return template_str
        
    def resolve_variables(self, template_str: str, variables: dict) -> str:
        def repl(match):
            var_name = match.group(1).strip()
            val = variables.get(var_name)
            if val is not None:
                return str(val)
            return f"{{{{{var_name}}}}}"
            
        return re.sub(r'\{\{([^#>/][^}]*)\}\}', repl, template_str)

    def build(self, template_name: str, variables: dict) -> str:
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
