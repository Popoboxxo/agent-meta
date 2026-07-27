import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# Replace viewProjectGitignore entirely
old_func_match = re.search(r'async function viewProjectGitignore\(\) \{.*?(?=\/\* ------------------------------- Gitignore Defaults ------------------------------ \*\/)', content, re.DOTALL)

if not old_func_match:
    print("Could not find viewProjectGitignore")
    exit(1)

new_func = """async function viewProjectGitignore() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project — Gitignore Rules"]));
  
  const helpText = el("p", { class: "help-text" }, ["Configure which agent-meta files and directories should be added to your host project's .gitignore file. Click on a category to set detailed exceptions for specific files."]);
  wrap.appendChild(helpText);

  let p;
  try {
    p = await api.get("/api/config/project");
  } catch (err) {
    wrap.appendChild(renderError(err));
    return wrap;
  }
  
  const current = p.gitignore || {};
  const defLocal = true;
  const defGenerated = false;
  const defSettings = false;

  const currentLocal = current.local !== undefined ? current.local : defLocal;
  const currentGenerated = current.generated !== undefined ? current.generated : defGenerated;
  const currentSettings = current.settings !== undefined ? current.settings : defSettings;
  const exceptions = current.exceptions || [];

  // Helper to determine if a specific path is ignored
  const isIgnored = (path, catDefault) => exceptions.includes(path) ? !catDefault : catDefault;
  
  // Calculate known paths dynamically based on active AI providers
  const activeProviders = p["ai-providers"] || ["Claude"];
  const getProvPrefix = (name) => name === "Claude" ? ".claude" : name === "Copilot" ? ".github/copilot" : `.${name.toLowerCase()}`;
  
  const knownLocal = [".claude/settings.local.json", ".claude/agent-memory-local/", "CLAUDE.personal.md", "sync.log"];
  const knownGenerated = [];
  const knownSettings = [];
  
  activeProviders.forEach(prov => {
    const pfx = getProvPrefix(prov);
    knownGenerated.push(`${pfx}/agents/`, `${pfx}/rules/`, `${pfx}/hooks/`, `${pfx}/commands/`);
    
    if (prov === "Claude") knownSettings.push(`${pfx}/settings.json`);
    else if (prov === "Gemini") knownSettings.push("GEMINI.md");
    else if (prov === "Opencode") knownSettings.push("opencode.json");
    else knownSettings.push(`${prov.toUpperCase()}.md`);
  });

  // Keep track of the current UI state for exceptions
  const currentExceptions = new Set(exceptions);

  const toggleException = (path, catDefault, isChecked) => {
    const wouldBeIgnored = isChecked;
    if (wouldBeIgnored !== catDefault) {
      currentExceptions.add(path); // It's an exception to the rule
    } else {
      currentExceptions.delete(path); // It follows the rule
    }
  };

  const renderCategory = (title, desc, catDefault, isChecked, paths) => {
    const container = el("div", { class: "panel", style: "margin-bottom: 12px; padding: 12px;" });
    
    // Header
    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
    const leftTitle = el("div", {}, [
      el("strong", {style:"font-size:14px;"}, [title]),
      el("div", { style: "font-size:12px; color:var(--text-muted); margin-top:4px;" }, [desc])
    ]);
    const rightToggle = el("div", { style: "display:flex; align-items:center; gap:8px;" });
    rightToggle.appendChild(el("span", { class: "badge badge-warning", style: "padding:4px 8px; border-radius:4px; font-size:11px; background-color:#d97706; color:#ffffff" }, [catDefault ? "Framework: Ignored" : "Framework: Committed"]));
    
    const globalCheckbox = el("input", { type: "checkbox", checked: isChecked });
    globalCheckbox.onchange = (e) => {
        const val = e.target.checked;
        // if global changes, we should probably clear exceptions for this group to avoid confusion
        paths.forEach(p => currentExceptions.delete(p));
        // Force re-render of this section by calling the main render again (naive but effective)
        // Actually, we'll just handle it on Save.
    };
    rightToggle.appendChild(globalCheckbox);
    header.appendChild(leftTitle);
    header.appendChild(rightToggle);
    container.appendChild(header);

    // Accordion details
    const details = document.createElement("details");
    details.style.marginTop = "12px";
    details.style.borderTop = "1px solid var(--border)";
    details.style.paddingTop = "12px";
    
    const summary = document.createElement("summary");
    summary.style.cursor = "pointer";
    summary.style.fontSize = "13px";
    summary.style.color = "var(--accent)";
    summary.innerText = "Show detailed files...";
    details.appendChild(summary);

    const list = el("div", { style: "margin-top:12px; display:grid; grid-template-columns: 1fr 1fr; gap:8px;" });
    paths.forEach(path => {
      const isPathIgnored = isIgnored(path, isChecked);
      const row = el("label", { style: "display:flex; align-items:center; gap:8px; font-family:var(--font-mono); font-size:12px;" });
      const cb = el("input", { type: "checkbox", checked: isPathIgnored });
      cb.onchange = (e) => {
         // evaluate against the global Checkbox state at time of save
         toggleException(path, globalCheckbox.checked, e.target.checked);
      };
      row.appendChild(cb);
      row.appendChild(document.createTextNode(path));
      list.appendChild(row);
    });
    details.appendChild(list);
    container.appendChild(details);

    return { container, getChecked: () => globalCheckbox.checked };
  };

  const localSection = renderCategory("Local Files", ".claude/settings.local.json, CLAUDE.personal.md, memory-local folders.", defLocal, currentLocal, knownLocal);
  const genSection = renderCategory("Generated Framework", "Provider folders (.claude/agents, .gemini/rules, etc.).", defGenerated, currentGenerated, knownGenerated);
  const setSection = renderCategory("Settings & Configs", "opencode.json, settings.json, config.yaml, etc.", defSettings, currentSettings, knownSettings);

  wrap.appendChild(localSection.container);
  wrap.appendChild(genSection.container);
  wrap.appendChild(setSection.container);

  // Custom paths section
  const customEntries = current.custom_entries || [];
  wrap.appendChild(el("h3", { style: "margin-top:24px;" }, ["Custom Paths"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Add any other files or directories you want agent-meta to manage in your .gitignore file. One path per line."]));
  
  const customTextArea = el("textarea", { 
    id: "git-custom", 
    style: "width:100%; height:120px; font-family:var(--font-mono); font-size:13px; padding:12px; border:1px solid var(--border); border-radius:6px; background:var(--bg-card); color:var(--text);",
    placeholder: ".claude/my-custom-folder/\\nsome-other-file.txt"
  });
  customTextArea.value = customEntries.join("\\n");
  wrap.appendChild(customTextArea);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top: 20px;" }, ["Save Gitignore Rules"]);
  saveBtn.onclick = async () => {
    saveBtn.disabled = true;
    
    // Parse custom paths
    const lines = document.getElementById("git-custom").value.split("\\n");
    const parsedCustom = lines.map(l => l.trim()).filter(l => l.length > 0);
    
    const data = {
      local: localSection.getChecked(),
      generated: genSection.getChecked(),
      settings: setSection.getChecked(),
      exceptions: Array.from(currentExceptions),
      custom_entries: parsedCustom
    };

    try {
      await api.put("/api/config/project/section", { section: "gitignore", data });
      toast("Gitignore rules saved! Run sync.py to apply.", "success");
      router.navigate("/project/gitignore");
    } catch (err) {
      toast("Error saving: " + err.message, "error");
    } finally {
      saveBtn.disabled = false;
    }
  };
  wrap.appendChild(saveBtn);
  return wrap;
}
"""
content = content.replace(old_func_match.group(0), new_func)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Gitignore Exceptions UI Patched")
