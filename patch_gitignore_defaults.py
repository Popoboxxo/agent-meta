import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# Ich brauche die gesamte viewProjectGitignore und viewGitignoreDefaults neu.
# Da viewProjectGitignore schon ziemlich groß ist, replace ich den gesamten Block von 'async function viewProjectGitignore()' bis vor 'async function viewProjectAdvanced()'.

old_match = re.search(r'async function viewProjectGitignore\(\) \{.*?(?=\/\* ------------------------------- Advanced -------------------------------- \*\/)', content, re.DOTALL)

new_code = """async function viewProjectGitignore() {
  const wrap = el("div");
  
  const topHeader = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
  topHeader.appendChild(el("h1", {}, ["Project — Gitignore Rules"]));
  const toggleAllBtn = el("button", { class: "btn btn-sm" }, ["Expand / Collapse All Details"]);
  toggleAllBtn.onclick = () => {
     const allDetails = wrap.querySelectorAll("details");
     if(allDetails.length === 0) return;
     const targetState = !allDetails[0].open;
     allDetails.forEach(d => d.open = targetState);
  };
  topHeader.appendChild(toggleAllBtn);
  wrap.appendChild(topHeader);
  
  const helpText = el("p", { class: "help-text" }, ["Configure which agent-meta files and directories should be added to your host project's .gitignore file."]);
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

  const isIgnored = (path, catDefault) => exceptions.includes(path) ? !catDefault : catDefault;
  
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

  const makeToggle = (ignored, onChange, readonly = false) => {
     let isIgnored = ignored;
     const w = el("div", { style: "display:flex; border: 1px solid var(--border); border-radius: 4px; overflow: hidden; font-size: 11px; user-select: none;" });
     const btnIgnore = el("div", { style: `padding: 4px 12px; transition: all 0.2s; ${readonly ? "opacity:0.8; cursor:not-allowed;" : "cursor:pointer;"} ${isIgnored ? "background: #2563eb; color: white; font-weight:bold;" : "background: var(--bg-card); color: var(--text-muted);"}` }, ["IGNORED"]);
     const btnTrack = el("div", { style: `padding: 4px 12px; transition: all 0.2s; ${readonly ? "opacity:0.8; cursor:not-allowed;" : "cursor:pointer;"} ${!isIgnored ? "background: #d97706; color: white; font-weight:bold;" : "background: var(--bg-card); color: var(--text-muted);"}` }, ["TRACKED"]);
     
     const setUI = (val) => {
         btnIgnore.style.background = val ? "#2563eb" : "var(--bg-card)";
         btnIgnore.style.color = val ? "white" : "var(--text-muted)";
         btnIgnore.style.fontWeight = val ? "bold" : "normal";
         
         btnTrack.style.background = !val ? "#d97706" : "var(--bg-card)";
         btnTrack.style.color = !val ? "white" : "var(--text-muted)";
         btnTrack.style.fontWeight = !val ? "bold" : "normal";
     };
  
     if (!readonly) {
         btnIgnore.onclick = () => { if(!isIgnored) { isIgnored = true; setUI(true); onChange(true); } };
         btnTrack.onclick = () => { if(isIgnored) { isIgnored = false; setUI(false); onChange(false); } };
     }
     
     w.appendChild(btnIgnore);
     w.appendChild(btnTrack);
     
     return { element: w, setValue: (val) => { isIgnored = val; setUI(val); }, getValue: () => isIgnored };
  };

  const renderCategory = (title, desc, catDefault, isChecked, paths) => {
    const container = el("div", { class: "panel", style: "margin-bottom: 12px; padding: 12px;" });
    
    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
    const leftTitle = el("div", {}, [
      el("strong", {style:"font-size:14px;"}, [title]),
      el("div", { style: "font-size:12px; color:var(--text-muted); margin-top:4px;" }, [desc])
    ]);
    const rightToggleWrap = el("div", { style: "display:flex; align-items:center; gap:12px;" });
    
    rightToggleWrap.appendChild(el("span", { class: "badge", style: `padding:4px 8px; border-radius:4px; font-size:11px; ${catDefault ? "background-color:rgba(37,99,235,0.2); color:#60a5fa;" : "background-color:rgba(217,119,6,0.2); color:#fbbf24;"}` }, [catDefault ? "Framework: Ignored" : "Framework: Tracked"]));
    
    const childrenToggles = []; 

    const parentToggle = makeToggle(isChecked, (newVal) => {
        childrenToggles.forEach(ct => ct.setValue(newVal));
    });

    rightToggleWrap.appendChild(parentToggle.element);
    header.appendChild(leftTitle);
    header.appendChild(rightToggleWrap);
    container.appendChild(header);

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

    const list = el("div", { style: "margin-top:12px; display:flex; flex-direction:column; gap:12px;" });
    paths.forEach(path => {
      const isPathIgnored = isIgnored(path, isChecked);
      const row = el("div", { style: "display:flex; align-items:center; justify-content:space-between; font-family:var(--font-mono); font-size:12px; padding: 4px 8px; background: var(--bg-body); border-radius:4px;" });
      
      row.appendChild(el("span", {}, [path]));
      
      const childToggle = makeToggle(isPathIgnored, (newVal) => {
          // No-op for exceptions, computed on save
      });
      childrenToggles.push(childToggle);
      
      row.appendChild(childToggle.element);
      list.appendChild(row);
    });
    details.appendChild(list);
    container.appendChild(details);

    return { 
        container, 
        getGlobalValue: () => parentToggle.getValue(),
        computeExceptions: () => {
            const exceptionsFound = [];
            const glob = parentToggle.getValue();
            paths.forEach((p, idx) => {
                if (childrenToggles[idx].getValue() !== glob) {
                    exceptionsFound.push(p);
                }
            });
            return exceptionsFound;
        }
    };
  };

  const localSection = renderCategory("Local Files", ".claude/settings.local.json, CLAUDE.personal.md, memory-local folders.", defLocal, currentLocal, knownLocal);
  const genSection = renderCategory("Generated Framework", "Provider folders (.claude/agents, .gemini/rules, etc.).", defGenerated, currentGenerated, knownGenerated);
  const setSection = renderCategory("Settings & Configs", "opencode.json, settings.json, config.yaml, etc.", defSettings, currentSettings, knownSettings);

  wrap.appendChild(localSection.container);
  wrap.appendChild(genSection.container);
  wrap.appendChild(setSection.container);

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
    const lines = document.getElementById("git-custom").value.split("\\n");
    const parsedCustom = lines.map(l => l.trim()).filter(l => l.length > 0);
    
    const finalExceptions = [
        ...localSection.computeExceptions(),
        ...genSection.computeExceptions(),
        ...setSection.computeExceptions()
    ];

    const data = {
      local: localSection.getGlobalValue(),
      generated: genSection.getGlobalValue(),
      settings: setSection.getGlobalValue(),
      exceptions: finalExceptions,
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

/* ------------------------------- Gitignore Defaults ------------------------------ */
async function viewGitignoreDefaults() {
  const wrap = el("div");
  
  const topHeader = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
  topHeader.appendChild(el("h1", {}, ["Framework Defaults — Gitignore Rules"]));
  const toggleAllBtn = el("button", { class: "btn btn-sm" }, ["Expand / Collapse All Details"]);
  toggleAllBtn.onclick = () => {
     const allDetails = wrap.querySelectorAll("details");
     if(allDetails.length === 0) return;
     const targetState = !allDetails[0].open;
     allDetails.forEach(d => d.open = targetState);
  };
  topHeader.appendChild(toggleAllBtn);
  wrap.appendChild(topHeader);
  
  const helpText = el("p", { class: "help-text" }, ["These are the standard Gitignore rules enforced by agent-meta. You can override them in your Project instance."]);
  wrap.appendChild(helpText);

  // We use same renderer but readonly
  const makeToggle = (ignored) => {
     const w = el("div", { style: "display:flex; border: 1px solid var(--border); border-radius: 4px; overflow: hidden; font-size: 11px; user-select: none;" });
     const btnIgnore = el("div", { style: `padding: 4px 12px; opacity:0.8; cursor:not-allowed; ${ignored ? "background: #2563eb; color: white; font-weight:bold;" : "background: var(--bg-card); color: var(--text-muted);"}` }, ["IGNORED"]);
     const btnTrack = el("div", { style: `padding: 4px 12px; opacity:0.8; cursor:not-allowed; ${!ignored ? "background: #d97706; color: white; font-weight:bold;" : "background: var(--bg-card); color: var(--text-muted);"}` }, ["TRACKED"]);
     w.appendChild(btnIgnore);
     w.appendChild(btnTrack);
     return w;
  };

  const renderReadonlyCategory = (title, desc, isChecked, paths) => {
    const container = el("div", { class: "panel", style: "margin-bottom: 12px; padding: 12px;" });
    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
    const leftTitle = el("div", {}, [
      el("strong", {style:"font-size:14px;"}, [title]),
      el("div", { style: "font-size:12px; color:var(--text-muted); margin-top:4px;" }, [desc])
    ]);
    header.appendChild(leftTitle);
    header.appendChild(makeToggle(isChecked));
    container.appendChild(header);

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

    const list = el("div", { style: "margin-top:12px; display:flex; flex-direction:column; gap:12px;" });
    paths.forEach(path => {
      const row = el("div", { style: "display:flex; align-items:center; justify-content:space-between; font-family:var(--font-mono); font-size:12px; padding: 4px 8px; background: var(--bg-body); border-radius:4px;" });
      row.appendChild(el("span", {}, [path]));
      row.appendChild(makeToggle(isChecked));
      list.appendChild(row);
    });
    details.appendChild(list);
    container.appendChild(details);
    return container;
  };

  const defLocal = true;
  const defGenerated = false;
  const defSettings = false;
  
  // We mock a standard set of paths for the default view
  const knownLocal = [".claude/settings.local.json", ".claude/agent-memory-local/", "CLAUDE.personal.md", "sync.log"];
  const knownGenerated = [".claude/agents/", ".claude/rules/", ".claude/hooks/", ".claude/commands/"];
  const knownSettings = [".claude/settings.json"];

  wrap.appendChild(renderReadonlyCategory("Local Files", ".claude/settings.local.json, CLAUDE.personal.md, memory-local folders.", defLocal, knownLocal));
  wrap.appendChild(renderReadonlyCategory("Generated Framework", "Provider folders (.claude/agents, .gemini/rules, etc.).", defGenerated, knownGenerated));
  wrap.appendChild(renderReadonlyCategory("Settings & Configs", "opencode.json, settings.json, config.yaml, etc.", defSettings, knownSettings));

  return wrap;
}

"""

if old_match:
    content = content.replace(old_match.group(0), new_code)
    with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Gitignore UX Defaults and Expand-All toggles added.")
else:
    print("Could not find viewProjectGitignore in second pass.")
