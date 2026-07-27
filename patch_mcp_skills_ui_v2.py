import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# --- 1. MCP Overrides ---
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
      
      // Deep merge connection block
      const fwConn = fw.connection || {};
      const ovConn = ov.connection || {};
      return { 
          ...fw, 
          ...ov, 
          connection: { ...fwConn, ...ovConn } 
      };
  };

  // UI Helpers
  const renderDictEditor = (title, dictData, onChange) => {
      const w = el("div", { style: "margin-top: 8px;" });
      w.appendChild(el("label", {}, [title]));
      const list = el("div", { style: "display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px;" });
      
      const renderRows = () => {
          list.innerHTML = "";
          Object.entries(dictData).forEach(([k, v]) => {
              const row = el("div", { style: "display: flex; gap: 4px;" });
              const inpK = el("input", { class: "form-control", value: k, style: "flex: 1;", placeholder: "Key" });
              const inpV = el("input", { class: "form-control", value: v, style: "flex: 2;", placeholder: "Value" });
              const btnDel = el("button", { class: "btn btn-danger btn-sm" }, ["×"]);
              
              inpK.onchange = (e) => { 
                  delete dictData[k]; 
                  if(e.target.value) dictData[e.target.value] = inpV.value; 
                  onChange(); renderRows(); 
              };
              inpV.oninput = (e) => { dictData[inpK.value] = e.target.value; onChange(); };
              btnDel.onclick = () => { delete dictData[k]; onChange(); renderRows(); };
              
              row.appendChild(inpK); row.appendChild(inpV); row.appendChild(btnDel);
              list.appendChild(row);
          });
      };
      renderRows();
      w.appendChild(list);
      const btnAdd = el("button", { class: "btn btn-sm" }, ["+ Add " + title]);
      btnAdd.onclick = () => { dictData["NEW_KEY"] = ""; onChange(); renderRows(); };
      w.appendChild(btnAdd);
      return w;
  };

  const renderArrayEditor = (title, arrData, onChange) => {
      const w = el("div", { style: "margin-top: 8px;" });
      w.appendChild(el("label", {}, [title]));
      const list = el("div", { style: "display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px;" });
      
      const renderRows = () => {
          list.innerHTML = "";
          arrData.forEach((v, idx) => {
              const row = el("div", { style: "display: flex; gap: 4px;" });
              const inpV = el("input", { class: "form-control", value: v, style: "flex: 1;", placeholder: "Argument" });
              const btnDel = el("button", { class: "btn btn-danger btn-sm" }, ["×"]);
              
              inpV.oninput = (e) => { arrData[idx] = e.target.value; onChange(); };
              btnDel.onclick = () => { arrData.splice(idx, 1); onChange(); renderRows(); };
              
              row.appendChild(inpV); row.appendChild(btnDel);
              list.appendChild(row);
          });
      };
      renderRows();
      w.appendChild(list);
      const btnAdd = el("button", { class: "btn btn-sm" }, ["+ Add Arg"]);
      btnAdd.onclick = () => { arrData.push(""); onChange(); renderRows(); };
      w.appendChild(btnAdd);
      return w;
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

    const conn = merged.connection || {};
    
    // Readonly View
    isReadonly.appendChild(el("div", {style:"color:#fff; font-weight:bold; margin-bottom:4px;"}, [`Type: ${conn.type || "unknown"}`]));
    if (conn.type === "stdio") {
        isReadonly.appendChild(el("div", {}, [`Command: ${conn.command || ""}`]));
        if (conn.args) isReadonly.appendChild(el("div", {}, [`Args: ${conn.args.join(" ")}`]));
        if (conn.env) {
           isReadonly.appendChild(el("div", {style:"margin-top:4px"}, ["Environment:"]));
           Object.entries(conn.env).forEach(([k,v]) => {
              isReadonly.appendChild(el("div", {style:"padding-left:8px;"}, [`${k}=${v}`]));
           });
        }
    } else if (conn.type === "sse") {
        isReadonly.appendChild(el("div", {}, [`URL: ${conn.url || ""}`]));
        if (conn.headers) {
           isReadonly.appendChild(el("div", {style:"margin-top:4px"}, ["Headers:"]));
           Object.entries(conn.headers).forEach(([k,v]) => {
              isReadonly.appendChild(el("div", {style:"padding-left:8px;"}, [`${k}: ${v}`]));
           });
        }
    }

    // Edit View
    const setupEditState = () => {
        if (!projOverrides[id]) {
            // Deep copy framework state to override
            projOverrides[id] = JSON.parse(JSON.stringify(fwServers[id] || {}));
            if (!projOverrides[id].connection) projOverrides[id].connection = { type: conn.type || "stdio" };
        }
        return projOverrides[id].connection;
    };

    if (conn.type === "stdio") {
        const wrapCmd = el("div", {});
        wrapCmd.appendChild(el("label", {}, ["Command"]));
        const inpCmd = el("input", { class: "form-control", value: conn.command || "" });
        inpCmd.oninput = (e) => { const c = setupEditState(); c.command = e.target.value; markDirty(); };
        wrapCmd.appendChild(inpCmd);
        isEditing.appendChild(wrapCmd);

        // Args editor
        const localArgs = conn.args ? [...conn.args] : [];
        isEditing.appendChild(renderArrayEditor("Arguments", localArgs, () => {
            const c = setupEditState();
            c.args = localArgs;
            markDirty();
        }));

        // Env editor
        const localEnv = conn.env ? { ...conn.env } : {};
        isEditing.appendChild(renderDictEditor("Environment Variables", localEnv, () => {
            const c = setupEditState();
            c.env = localEnv;
            markDirty();
        }));

    } else if (conn.type === "sse") {
        const wrapUrl = el("div", {});
        wrapUrl.appendChild(el("label", {}, ["URL"]));
        const inpUrl = el("input", { class: "form-control", value: conn.url || "" });
        inpUrl.oninput = (e) => { const c = setupEditState(); c.url = e.target.value; markDirty(); };
        wrapUrl.appendChild(inpUrl);
        isEditing.appendChild(wrapUrl);

        // Headers editor
        const localHeaders = conn.headers ? { ...conn.headers } : {};
        isEditing.appendChild(renderDictEditor("Headers", localHeaders, () => {
            const c = setupEditState();
            c.headers = localHeaders;
            markDirty();
        }));
    } else {
         isEditing.appendChild(el("div", {}, ["Unsupported connection type for UI editing."]));
    }

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
      projOverrides[id] = { connection: { type: "stdio", command: "", args: [] } };
      activeServers.add(id);
      markDirty();
      toast("Custom server added to state. Click save below to apply.", "info");
    }
  };
  wrap.appendChild(addBtn);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top:20px; display:block; width: 100%" }, ["Save Project MCP Configuration"]);
  saveBtn.onclick = async () => {
    try {
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

# --- 2. Skills Overrides ---
old_skills_match = re.search(r'async function viewProjectSkillsOverrides\(\) \{.*?(?=async function viewMcpRegistry)', content, re.DOTALL)
new_skills = """async function viewProjectSkillsOverrides() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project Skills Configuration"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Enable/Disable Framework Skills for your project, or customize them specifically for this repository."]));

  let projData, fwData;
  try {
    projData = await api.get("/api/config/project");
    fwData = await api.get("/api/config/skills-registry").catch(() => ({ skills: {}, repos: {} }));
  } catch (err) {
    wrap.appendChild(renderError(err));
    return wrap;
  }
  
  const activeSkills = new Set(projData["external-skills"] || []);
  const projOverrides = projData["skills-registry"] || {};
  const fwSkills = fwData.skills || {};
  const fwRepos = fwData.repos || {};

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
    
    // Look up pinned commit from repo if not overridden
    const repoId = merged.repo;
    const fwRepoInfo = fwRepos[repoId] || {};
    const recommendedVersion = fwRepoInfo.pinned_commit || "main";
    const currentVersion = merged.version || recommendedVersion;

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

    const repoUrl = fwRepoInfo.repo ? fwRepoInfo.repo : (merged.repo || "");
    isReadonly.appendChild(el("div", {}, [`Repo: ${repoUrl}`]));
    
    // Display version with Recommended badge if it matches
    const verWrap = el("div", {style:"display:flex; align-items:center; gap: 8px;"});
    verWrap.appendChild(el("span", {}, [`Version: ${currentVersion}`]));
    if (currentVersion === recommendedVersion && isFramework) {
        verWrap.appendChild(el("span", { class: "badge", style:"background-color:#4f46e5; color:#fff" }, ["Recommended Tag"]));
    } else if (isFramework) {
        verWrap.appendChild(el("span", { class: "badge badge-warning" }, [`Warning: Framework recommends ${recommendedVersion}`]));
    }
    isReadonly.appendChild(verWrap);
    
    // Edit View
    const mkInput = (labelTxt, key, defaultVal) => {
      const lbl = el("label", {}, [labelTxt]);
      const inp = el("input", { type: "text", class: "form-control", value: merged[key] || defaultVal });
      inp.oninput = (e) => {
          if (!projOverrides[id]) projOverrides[id] = { ...fwSkills[id] };
          projOverrides[id][key] = e.target.value;
          markDirty();
      };
      const w = el("div", {}, [lbl, inp]);
      isEditing.appendChild(w);
    };
    mkInput("Repo ID / URL", "repo", repoUrl);
    mkInput(`Version (Branch/Tag) - Framework default: ${recommendedVersion}`, "version", currentVersion);

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

if old_skills_match:
    content = content.replace(old_skills_match.group(0), new_skills)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("UI Refinements Applied")
