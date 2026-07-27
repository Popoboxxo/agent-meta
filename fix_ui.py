import sys

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the implementation of viewProjectGitignore
old_func = """async function viewProjectGitignore() {
  const wrap = document.getElementById("content");
  wrap.innerHTML = "";"""

new_func = """async function viewProjectGitignore() {
  const wrap = el("div");"""

content = content.replace(old_func, new_func)

# Add return statement and router call to viewProjectGitignore
# By replacing the end of viewProjectGitignore
old_end = """    } finally {
      saveBtn.disabled = false;
    }
  };
  wrap.appendChild(saveBtn);
}"""

new_end = """    } finally {
      saveBtn.disabled = false;
    }
  };
  wrap.appendChild(saveBtn);
  return wrap;
}

/* ------------------------------- Gitignore Defaults ------------------------------ */
async function viewGitignoreDefaults() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Framework Defaults — Gitignore Rules"]));
  
  const helpText = el("p", { class: "help-text" }, ["These are the standard Gitignore rules enforced by agent-meta. You can override them in your Project instance."]);
  wrap.appendChild(helpText);

  const table = el("table", { class: "data-table" });
  table.innerHTML = `
    <thead>
      <tr>
        <th>Category</th>
        <th>Description</th>
        <th>Framework Default</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Local Files</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">.claude/settings.local.json, CLAUDE.personal.md, memory-local folders.</td>
        <td><span class="badge badge-success" style="padding:4px 8px; border-radius:4px; font-size:11px">Ignored</span></td>
      </tr>
      <tr>
        <td><strong>Generated Framework</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">Provider folders (.claude/agents, .gemini/rules, etc.).</td>
        <td><span class="badge badge-warning" style="padding:4px 8px; border-radius:4px; font-size:11px; background:var(--accent-orange); color:#111">Committed</span></td>
      </tr>
      <tr>
        <td><strong>Settings & Configs</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">opencode.json, settings.json, config.yaml, etc.</td>
        <td><span class="badge badge-warning" style="padding:4px 8px; border-radius:4px; font-size:11px; background:var(--accent-orange); color:#111">Committed</span></td>
      </tr>
    </tbody>
  `;
  wrap.appendChild(table);
  return wrap;
}
"""

content = content.replace(old_end, new_end)

# Fix await viewProjectGitignore() -> re-routing in save button
old_save_rerender = 'await viewProjectGitignore();'
new_save_rerender = 'router.navigate("/project/gitignore");'
content = content.replace(old_save_rerender, new_save_rerender)

# Add nav entry for framework defaults
old_nav = '        { route: "/models", label: "Models & Pricing", icon: "💲", superOnly: true },'
new_nav = '        { route: "/models", label: "Models & Pricing", icon: "💲", superOnly: true },\n        { route: "/config/gitignore-defaults", label: "Gitignore Defaults", icon: "🚫", superOnly: true },'
content = content.replace(old_nav, new_nav)

# Add route for framework defaults
old_route = '  router.register("/config/project",  viewProjectAdvanced);'
new_route = '  router.register("/config/project",  viewProjectAdvanced);\n  router.register("/config/gitignore-defaults", viewGitignoreDefaults);'
content = content.replace(old_route, new_route)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Fix applied")
