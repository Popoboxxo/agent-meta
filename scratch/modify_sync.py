import re

with open('scripts/sync.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find the end of the `for provider in providers:` block
# We can look for `sync_agents_for_provider(...)` or `sync_context_for_provider(...)` inside that loop.
# It is around line 919:
#             sync_context_for_provider(agent_meta_root, project_root, config, provider_variables,
#                                       log, args.dry_run, provider, provider_config)

search_str = "sync_context_for_provider(agent_meta_root, project_root, config, provider_variables,\n                                      log, args.dry_run, provider, provider_config)"
if search_str not in content:
    print("Could not find the hook location.")
else:
    cleanup_code = """
        # Cleanup legacy files for removed providers
        all_known_providers = provider_config.keys()
        for prov in all_known_providers:
            if prov == "providers": continue # Skip the top-level key if present
            if prov not in providers:
                pc = provider_config.get(prov, {})
                
                # Default paths if missing from config
                a_dir = pc.get("agents_dir", f".{prov.lower()}/agents")
                c_file = pc.get("context_file", f"{prov.upper()}.md")
                if c_file == "CLAUDE.md" and prov != "Claude":
                    # E.g. Opencode uses AGENTS.md, fallback
                    c_file = "AGENTS.md"
                
                agents_dir = project_root / a_dir
                context_file = project_root / c_file
                
                if agents_dir.exists():
                    log.action("DELETE", str(agents_dir.relative_to(project_root)), f"provider {prov} removed")
                    if not args.dry_run:
                        import shutil
                        shutil.rmtree(agents_dir)
                if context_file.exists():
                    log.action("DELETE", str(context_file.relative_to(project_root)), f"provider {prov} removed")
                    if not args.dry_run:
                        context_file.unlink()
"""
    
    # insert after search_str
    parts = content.split(search_str)
    new_content = parts[0] + search_str + cleanup_code + parts[1]
    with open('scripts/sync.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Injected cleanup logic.")
