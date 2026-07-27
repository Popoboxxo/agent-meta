import sys

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

target = "/* ------------------------------- Advanced -------------------------------- */"
new_content = """/* ------------------------------- Gitignore ------------------------------- */
async function viewProjectGitignore() {
  const wrap = document.getElementById("content");
  wrap.innerHTML = "";
  wrap.appendChild(el("h1", {}, ["Project — Gitignore Rules"]));
  
  const helpText = el("p", { class: "help-text" }, ["Configure which agent-meta files and directories should be added to your host project's .gitignore file. The Framework Defaults are recommended, but you can override them here."]);
  wrap.appendChild(helpText);

  let p;
  try {
    p = await api.get("/api/config/project");
  } catch (err) {
    wrap.appendChild(renderError(err));
    return;
  }
  const current = p.gitignore || {};
  // Default values
  const defLocal = true;
  const defGenerated = false;
  const defSettings = false;

  const currentLocal = current.local !== undefined ? current.local : defLocal;
  const currentGenerated = current.generated !== undefined ? current.generated : defGenerated;
  const currentSettings = current.settings !== undefined ? current.settings : defSettings;

  const table = el("table", { class: "data-table" });
  table.innerHTML = `
    <thead>
      <tr>
        <th>Category</th>
        <th>Description</th>
        <th>Framework Default</th>
        <th>Project Override (Gitignored)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Local Files</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">.claude/settings.local.json, CLAUDE.personal.md, memory-local folders.</td>
        <td><span class="badge badge-success" style="padding:4px 8px; border-radius:4px; font-size:11px">Ignored</span></td>
        <td><input type="checkbox" id="git-local" ${currentLocal ? "checked" : ""}></td>
      </tr>
      <tr>
        <td><strong>Generated Framework</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">Provider folders (.claude/agents, .gemini/rules, etc.).</td>
        <td><span class="badge badge-warning" style="padding:4px 8px; border-radius:4px; font-size:11px; background:var(--accent-orange); color:#111">Committed</span></td>
        <td><input type="checkbox" id="git-generated" ${currentGenerated ? "checked" : ""}></td>
      </tr>
      <tr>
        <td><strong>Settings & Configs</strong></td>
        <td style="font-size:12px; color:var(--text-muted)">opencode.json, settings.json, config.yaml, etc.</td>
        <td><span class="badge badge-warning" style="padding:4px 8px; border-radius:4px; font-size:11px; background:var(--accent-orange); color:#111">Committed</span></td>
        <td><input type="checkbox" id="git-settings" ${currentSettings ? "checked" : ""}></td>
      </tr>
    </tbody>
  `;
  wrap.appendChild(table);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top: 20px;" }, ["Save Gitignore Rules"]);
  saveBtn.onclick = async () => {
    saveBtn.disabled = true;
    const data = {
      local: document.getElementById("git-local").checked,
      generated: document.getElementById("git-generated").checked,
      settings: document.getElementById("git-settings").checked
    };
    try {
      await api.put("/api/config/project/section", { section: "gitignore", data });
      toast("Gitignore rules saved! Run sync.py to apply.", "success");
      await viewProjectGitignore();
    } catch (err) {
      toast("Error saving: " + err.message, "error");
    } finally {
      saveBtn.disabled = false;
    }
  };
  wrap.appendChild(saveBtn);
}

/* ------------------------------- Advanced -------------------------------- */"""

if target in content:
    new_text = content.replace(target, new_content, 1)
    
    # Also add the router
    router_target = 'router.register("/project/advanced",        viewProjectAdvanced);'
    router_new = router_target + '\n  router.register("/project/gitignore",       viewProjectGitignore);'
    new_text = new_text.replace(router_target, router_new, 1)
    
    with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Patched successfully")
else:
    print("Target not found")
