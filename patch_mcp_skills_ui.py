import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. MCP Overrides
old_mcp_match = re.search(r'async function viewProjectMcpOverrides\(\) \{.*?(?=async function viewProjectSkillsOverrides)', content, re.DOTALL)

new_mcp = """async function viewProjectMcpOverrides() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project MCP Configuration"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Enable/Disable Framework MCP servers for your project, or customize them specifically for this repository."]));

  let projData, fwData;
  try {
    projData = await api.get("/api/config/project");
    fwData = await api.get("/api/config/mcp-registry").catch(() => ({ "mcp-servers": {} }));
  } catch (err) {
    wrap.appendChild(renderError(err));
    return wrap;
  }
  
  const activeServers = new Set(projData["mcp-servers"] || []);
  const projOverrides = projData["mcp-registry"] || {};
  const fwServers = fwData["mcp-servers"] || {};

  let dirty = false;
  const markDirty = () => { dirty = true; };

  const getMerged = (id) => {
      const fw = fwServers[id] || {};
      const ov = projOverrides[id] || {};
      return { ...fw, ...ov };
  };

  const renderSrvPanel = (id, isFramework) => {
    const isOverride = projOverrides.hasOwnProperty(id);
    const isActive = activeServers.has(id);
    const merged = getMerged(id);

    const p = el("div", { class: "panel", style: "margin-bottom:12px;" });
    if (isOverride) p.style.borderLeft = "3px solid var(--accent)";

    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
    const titleBox = el("div", { style: "display:flex; align-items:center; gap: 8px;" });
    titleBox.appendChild(el("h3", { style: "margin:0" }, [id]));
    if (isFramework) titleBox.appendChild(el("span", { class: "badge badge-warning", style:"background-color:#0d9488; color:#fff" }, ["Framework Server"]));
    if (isOverride) titleBox.appendChild(el("span", { class: "badge badge-warning" }, ["Custom Override Active"]));
    header.appendChild(titleBox);

    const toggleBox = el("div", { style: "display:flex; align-items:center; gap: 8px;" });
    toggleBox.appendChild(document.createTextNode("Active in Project:"));
    const activeCb = el("input", { type: "checkbox", checked: isActive });
    activeCb.onchange = (e) => {
        if(e.target.checked) activeServers.add(id);
        else activeServers.delete(id);
        markDirty();
    };
    toggleBox.appendChild(activeCb);
    header.appendChild(toggleBox);
    p.appendChild(header);

    const detailsWrap = el("div", { style: "margin-top: 12px; display: flex; gap: 12px; flex-direction: column;" });
    const isEditing = el("div", { style: "display: none; flex-direction: column; gap: 12px; margin-top: 8px;" });
    const isReadonly = el("div", { style: "display: flex; flex-direction: column; gap: 4px; font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); padding: 8px; background: var(--bg-body); border-radius: 4px;" });

    isReadonly.appendChild(el("div", {}, [`Command: ${merged.command || ""}`]));
    isReadonly.appendChild(el("div", {}, [`Args: ${JSON.stringify(merged.args || [])}`]));
    
    const mkInput = (labelTxt, key) => {
      const lbl = el("label", {}, [labelTxt]);
      const inp = el("input", { type: "text", class: "form-control", value: key === "args" ? JSON.stringify(merged[key] || []) : (merged[key] || "") });
      inp.oninput = (e) => {
          if (!projOverrides[id]) projOverrides[id] = { ...fwServers[id] };
          if (key === "args") {
             try { projOverrides[id][key] = JSON.parse(e.target.value); } catch(err) {}
          } else {
             projOverrides[id][key] = e.target.value;
          }
          markDirty();
      };
      const w = el("div", {}, [lbl, inp]);
      isEditing.appendChild(w);
    };
    mkInput("Command", "command");
    mkInput("Args (JSON Array)", "args");

    detailsWrap.appendChild(isReadonly);
    detailsWrap.appendChild(isEditing);

    const actionBox = el("div", { style: "margin-top: 12px; display:flex; gap: 8px;" });
    const customizeBtn = el("button", { class: "btn btn-sm" }, [isOverride ? "Edit Override" : "Customize (Create Override)"]);
    customizeBtn.onclick = () => {
        isReadonly.style.display = "none";
        isEditing.style.display = "flex";
        customizeBtn.style.display = "none";
    };
    actionBox.appendChild(customizeBtn);

    if (isOverride) {
        const resetBtn = el("button", { class: "btn btn-danger btn-sm" }, ["Reset to Default"]);
        resetBtn.onclick = () => {
            delete projOverrides[id];
            markDirty();
            isReadonly.style.display = "flex";
            isEditing.style.display = "none";
            toast("Override removed. Click save to apply.", "info");
            p.style.borderLeft = "none";
        };
        actionBox.appendChild(resetBtn);
    }
    detailsWrap.appendChild(actionBox);
    p.appendChild(detailsWrap);
    return p;
  };

  const projListContainer = el("div", { style: "margin-bottom:24px" });
  
  const allIds = new Set([...Object.keys(fwServers), ...Object.keys(projOverrides)]);
  
  if (allIds.size === 0) {
    projListContainer.appendChild(el("div", { class: "muted" }, ["No servers found."]));
  } else {
    Array.from(allIds).sort().forEach(id => {
      projListContainer.appendChild(renderSrvPanel(id, fwServers.hasOwnProperty(id)));
    });
  }
  
  wrap.appendChild(projListContainer);

  const addBtn = el("button", { class: "btn" }, ["+ Add Custom Server (Not in Framework)"]);
  addBtn.onclick = () => {
    const id = prompt("MCP Server ID:");
    if (id && !allIds.has(id)) {
      projOverrides[id] = { command: "", args: [] };
      activeServers.add(id);
      markDirty();
      toast("Custom server added to state. Click save below to apply.", "info");
    }
  };
  wrap.appendChild(addBtn);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top:20px; display:block; width: 100%" }, ["Save Project MCP Configuration"]);
  saveBtn.onclick = async () => {
    try {
      const data = {
          "mcp-servers": Array.from(activeServers),
          "mcp-registry": projOverrides
      };
      await api.put("/api/config/project/section", { section: "mcp-servers", data }); // the endpoint handles both arrays via full object patch or section logic? 
      // Actually, my backend endpoint api.put("/api/config/project-mcp-registry") already exists and only touches mcp-registry. 
      // Let's use api.put("/api/config/project") to save everything.
      projData["mcp-servers"] = Array.from(activeServers);
      projData["mcp-registry"] = projOverrides;
      await api.put("/api/config/project", projData);
      toast("MCP configuration saved", "success");
      dirty = false;
      router.navigate("/project/mcp-overrides");
    } catch (e) {
      toast(e.message, "error");
    }
  };
  wrap.appendChild(saveBtn);

  return wrap;
}

"""
if old_mcp_match:
    content = content.replace(old_mcp_match.group(0), new_mcp)
else:
    print("Could not find viewProjectMcpOverrides")

# 2. Skills Overrides
old_skills_match = re.search(r'async function viewProjectSkillsOverrides\(\) \{.*?(?=async function viewMcpRegistry)', content, re.DOTALL)
if not old_skills_match:
    print("Could not find viewProjectSkillsOverrides")
    exit(1)

new_skills = """async function viewProjectSkillsOverrides() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project Skills Configuration"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Enable/Disable Framework Skills for your project, or customize them specifically for this repository."]));

  let projData, fwData;
  try {
    projData = await api.get("/api/config/project");
    fwData = await api.get("/api/config/skills-registry").catch(() => ({ skills: {} }));
  } catch (err) {
    wrap.appendChild(renderError(err));
    return wrap;
  }
  
  const activeSkills = new Set(projData["external-skills"] || []);
  const projOverrides = projData["skills-registry"] || {};
  const fwSkills = fwData.skills || {};

  let dirty = false;
  const markDirty = () => { dirty = true; };

  const getMerged = (id) => {
      const fw = fwSkills[id] || {};
      const ov = projOverrides[id] || {};
      return { ...fw, ...ov };
  };

  const renderSkillPanel = (id, isFramework) => {
    const isOverride = projOverrides.hasOwnProperty(id);
    const isActive = activeSkills.has(id);
    const merged = getMerged(id);

    const p = el("div", { class: "panel", style: "margin-bottom:12px;" });
    if (isOverride) p.style.borderLeft = "3px solid var(--accent)";

    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center;" });
    const titleBox = el("div", { style: "display:flex; align-items:center; gap: 8px;" });
    titleBox.appendChild(el("h3", { style: "margin:0" }, [id]));
    if (isFramework) titleBox.appendChild(el("span", { class: "badge badge-warning", style:"background-color:#0d9488; color:#fff" }, ["Framework Skill"]));
    if (isOverride) titleBox.appendChild(el("span", { class: "badge badge-warning" }, ["Custom Override Active"]));
    header.appendChild(titleBox);

    const toggleBox = el("div", { style: "display:flex; align-items:center; gap: 8px;" });
    toggleBox.appendChild(document.createTextNode("Active in Project:"));
    const activeCb = el("input", { type: "checkbox", checked: isActive });
    activeCb.onchange = (e) => {
        if(e.target.checked) activeSkills.add(id);
        else activeSkills.delete(id);
        markDirty();
    };
    toggleBox.appendChild(activeCb);
    header.appendChild(toggleBox);
    p.appendChild(header);

    const detailsWrap = el("div", { style: "margin-top: 12px; display: flex; gap: 12px; flex-direction: column;" });
    const isEditing = el("div", { style: "display: none; flex-direction: column; gap: 12px; margin-top: 8px;" });
    const isReadonly = el("div", { style: "display: flex; flex-direction: column; gap: 4px; font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); padding: 8px; background: var(--bg-body); border-radius: 4px;" });

    isReadonly.appendChild(el("div", {}, [`Repo: ${merged.repo || ""}`]));
    isReadonly.appendChild(el("div", {}, [`Version: ${merged.version || "main"}`]));
    
    const mkInput = (labelTxt, key) => {
      const lbl = el("label", {}, [labelTxt]);
      const inp = el("input", { type: "text", class: "form-control", value: merged[key] || "" });
      inp.oninput = (e) => {
          if (!projOverrides[id]) projOverrides[id] = { ...fwSkills[id] };
          projOverrides[id][key] = e.target.value;
          markDirty();
      };
      const w = el("div", {}, [lbl, inp]);
      isEditing.appendChild(w);
    };
    mkInput("Repo URL", "repo");
    mkInput("Version (Branch/Tag)", "version");

    detailsWrap.appendChild(isReadonly);
    detailsWrap.appendChild(isEditing);

    const actionBox = el("div", { style: "margin-top: 12px; display:flex; gap: 8px;" });
    const customizeBtn = el("button", { class: "btn btn-sm" }, [isOverride ? "Edit Override" : "Customize (Create Override)"]);
    customizeBtn.onclick = () => {
        isReadonly.style.display = "none";
        isEditing.style.display = "flex";
        customizeBtn.style.display = "none";
    };
    actionBox.appendChild(customizeBtn);

    if (isOverride) {
        const resetBtn = el("button", { class: "btn btn-danger btn-sm" }, ["Reset to Default"]);
        resetBtn.onclick = () => {
            delete projOverrides[id];
            markDirty();
            isReadonly.style.display = "flex";
            isEditing.style.display = "none";
            toast("Override removed. Click save to apply.", "info");
            p.style.borderLeft = "none";
        };
        actionBox.appendChild(resetBtn);
    }
    detailsWrap.appendChild(actionBox);
    p.appendChild(detailsWrap);
    return p;
  };

  const projListContainer = el("div", { style: "margin-bottom:24px" });
  
  const allIds = new Set([...Object.keys(fwSkills), ...Object.keys(projOverrides)]);
  
  if (allIds.size === 0) {
    projListContainer.appendChild(el("div", { class: "muted" }, ["No skills found."]));
  } else {
    Array.from(allIds).sort().forEach(id => {
      projListContainer.appendChild(renderSkillPanel(id, fwSkills.hasOwnProperty(id)));
    });
  }
  
  wrap.appendChild(projListContainer);

  const addBtn = el("button", { class: "btn" }, ["+ Add Custom Skill (Not in Framework)"]);
  addBtn.onclick = () => {
    const id = prompt("Skill ID:");
    if (id && !allIds.has(id)) {
      projOverrides[id] = { repo: "", version: "main" };
      activeSkills.add(id);
      markDirty();
      toast("Custom skill added. Click save below to apply.", "info");
    }
  };
  wrap.appendChild(addBtn);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top:20px; display:block; width: 100%" }, ["Save Project Skills Configuration"]);
  saveBtn.onclick = async () => {
    try {
      projData["external-skills"] = Array.from(activeSkills);
      projData["skills-registry"] = projOverrides;
      await api.put("/api/config/project", projData);
      toast("Skills configuration saved", "success");
      dirty = false;
      router.navigate("/project/skills-overrides");
    } catch (e) {
      toast(e.message, "error");
    }
  };
  wrap.appendChild(saveBtn);

  return wrap;
}

"""
content = content.replace(old_skills_match.group(0), new_skills)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("MCP & Skills UI Unified Patched")
