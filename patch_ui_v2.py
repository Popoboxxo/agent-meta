import sys
import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Navigationsmenü anpassen
old_nav_project = """        { route: "/project/gitignore", label: "Gitignore Rules", icon: "🚫" },
        { route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" },
      ],
    },"""
new_nav_project = """        { route: "/project/gitignore", label: "Gitignore Rules", icon: "🚫" },
        { route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" },
        { route: "/project/mcp-overrides", label: "MCP Overrides", icon: "🔌" },
        { route: "/project/skills-overrides", label: "Skills Overrides", icon: "🧩" },
      ],
    },"""
content = content.replace(old_nav_project, new_nav_project)

# 2. viewProjectGitignore anpassen (Textarea für Custom Paths hinzufügen)
old_gitignore_ui_end = """    </tbody>
  `;
  wrap.appendChild(table);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top: 20px;" }, ["Save Gitignore Rules"]);
  saveBtn.onclick = async () => {
    saveBtn.disabled = true;
    const data = {
      local: document.getElementById("git-local").checked,
      generated: document.getElementById("git-generated").checked,
      settings: document.getElementById("git-settings").checked
    };"""

new_gitignore_ui_end = """    </tbody>
  `;
  wrap.appendChild(table);

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
      local: document.getElementById("git-local").checked,
      generated: document.getElementById("git-generated").checked,
      settings: document.getElementById("git-settings").checked,
      custom_entries: parsedCustom
    };"""
content = content.replace(old_gitignore_ui_end, new_gitignore_ui_end)


# 3. viewMcpRegistry überschreiben (Nur Readonly Framework Defaults)
old_mcp = re.search(r'async function viewMcpRegistry\(\) \{.*?(?=async function viewSkillsRegistry)', content, re.DOTALL)
if old_mcp:
    new_mcp = """async function viewMcpRegistry() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["mcp-registry.yaml (Framework Defaults)"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["These are the global MCP servers configured in the framework. This view is read-only. Edit overrides in the Project Instance section."]));

  let fwData;
  try { fwData = await api.get("/api/config/mcp-registry").catch(() => ({ "mcp-servers": {} })); }
  catch (err) { wrap.appendChild(renderError(err)); return wrap; }

  const fwServers = fwData["mcp-servers"] || {};

  const renderSrvPanel = (id, srv) => {
    const p = el("div", { class: "panel", style: "margin-bottom:12px; border-left: 3px solid var(--accent-orange);" });
    p.appendChild(el("h3", { style: "margin-bottom:8px" }, [id, el("span", { class: "badge badge-warning", style: "margin-left:8px" }, ["Framework Default"])]));
    p.appendChild(el("div", { style: "font-family:var(--font-mono); font-size:12px; color:var(--text-muted)" }, [
      srv.command ? `Command: ${srv.command}` : "",
      srv.args ? ` Args: ${JSON.stringify(srv.args)}` : "",
      srv.env ? ` Env: ${JSON.stringify(srv.env)}` : ""
    ]));
    return p;
  };

  const fwListContainer = el("div", { style: "margin-bottom:24px" });
  if (Object.keys(fwServers).length === 0) {
    fwListContainer.appendChild(el("div", { class: "muted" }, ["No framework defaults."]));
  } else {
    for (const [id, srv] of Object.entries(fwServers)) {
      fwListContainer.appendChild(renderSrvPanel(id, srv));
    }
  }
  wrap.appendChild(fwListContainer);

  return wrap;
}

"""
    content = content.replace(old_mcp.group(0), new_mcp)

# 4. viewSkillsRegistry überschreiben (Nur Readonly Framework Defaults)
old_skills = re.search(r'async function viewSkillsRegistry\(\) \{.*?(?=async function viewSkillForm)', content, re.DOTALL)
if old_skills:
    new_skills = """async function viewSkillsRegistry() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["skills-registry.yaml (Framework Defaults)"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Global skills registered in the framework. This view is read-only."]));

  let fwData;
  try { fwData = await api.get("/api/config/skills-registry").catch(() => ({ skills: {} })); }
  catch (err) { wrap.appendChild(renderError(err)); return wrap; }

  const fwSkills = fwData.skills || {};

  const fwListContainer = el("div", { style: "margin-bottom:24px" });
  if (Object.keys(fwSkills).length === 0) {
    fwListContainer.appendChild(el("div", { class: "muted" }, ["No framework skills."]));
  } else {
    for (const [id, skill] of Object.entries(fwSkills)) {
      const p = el("div", { class: "panel", style: "margin-bottom:12px; border-left: 3px solid var(--accent-orange);" });
      p.appendChild(el("h3", { style: "margin-bottom:8px" }, [id, el("span", { class: "badge badge-warning", style: "margin-left:8px" }, ["Framework Default"])]));
      p.appendChild(el("div", { style: "font-family:var(--font-mono); font-size:12px; color:var(--text-muted)" }, [
        skill.repo ? `Repo: ${skill.repo}` : "",
        skill.approved ? " (Approved)" : " (Unapproved)"
      ]));
      fwListContainer.appendChild(p);
    }
  }
  wrap.appendChild(fwListContainer);

  return wrap;
}

"""
    content = content.replace(old_skills.group(0), new_skills)

# 5. Neue Funktionen viewProjectMcpOverrides und viewProjectSkillsOverrides hinzufügen
# Wir fügen sie einfach vor viewMcpRegistry ein
overrides_funcs = """async function viewProjectMcpOverrides() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project MCP Overrides"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Configure MCP server overrides specific to this project. These are stored in project.yaml."]));

  let projData;
  try { projData = await api.get("/api/config/project-mcp-registry").catch(() => ({ "mcp-servers": {} })); }
  catch (err) { projData = { "mcp-servers": {} }; }
  
  const projServers = projData["mcp-servers"] || {};
  let dirty = false;
  const markDirty = () => { dirty = true; renderProjList(); };

  const renderSrvPanel = (id, srv) => {
    const p = el("div", { class: "panel", style: "margin-bottom:12px;" });
    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;" });
    header.appendChild(el("h3", { style: "margin:0" }, [id]));
    const delBtn = el("button", { class: "btn btn-danger btn-sm" }, ["Delete"]);
    delBtn.onclick = () => { delete projServers[id]; markDirty(); };
    header.appendChild(delBtn);
    p.appendChild(header);

    const mkInput = (labelTxt, key, type = "text") => {
      const lbl = el("label", {}, [labelTxt]);
      const inp = el("input", { type, class: "form-control", value: srv[key] || "" });
      inp.oninput = (e) => { srv[key] = e.target.value; markDirty(); };
      p.appendChild(lbl); p.appendChild(inp);
    };
    mkInput("Command", "command");
    
    const lblArgs = el("label", {}, ["Args (JSON Array)"]);
    const inpArgs = el("input", { type: "text", class: "form-control", value: srv.args ? JSON.stringify(srv.args) : "[]" });
    inpArgs.onchange = (e) => { try { srv.args = JSON.parse(e.target.value); markDirty(); } catch(err) { toast("Invalid JSON", "error"); } };
    p.appendChild(lblArgs); p.appendChild(inpArgs);

    return p;
  };

  const projListContainer = el("div", { style: "margin-bottom:24px" });
  
  const renderProjList = () => {
    projListContainer.innerHTML = "";
    if (Object.keys(projServers).length === 0) {
      projListContainer.appendChild(el("div", { class: "muted" }, ["No project overrides."]));
    } else {
      for (const [id, srv] of Object.entries(projServers)) {
        projListContainer.appendChild(renderSrvPanel(id, srv));
      }
    }
  };
  
  renderProjList();
  wrap.appendChild(projListContainer);

  const addBtn = el("button", { class: "btn" }, ["+ Add Override"]);
  addBtn.onclick = () => {
    const id = prompt("MCP Server ID:");
    if (id && !projServers[id]) {
      projServers[id] = { command: "", args: [] };
      markDirty();
    }
  };
  wrap.appendChild(addBtn);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top:20px; display:block" }, ["Save Overrides"]);
  saveBtn.onclick = async () => {
    try {
      await api.put("/api/config/project-mcp-registry", { "mcp-servers": projServers });
      toast("MCP overrides saved", "success");
      dirty = false;
      router.navigate("/project/mcp-overrides");
    } catch (e) {
      toast(e.message, "error");
    }
  };
  wrap.appendChild(saveBtn);

  return wrap;
}

async function viewProjectSkillsOverrides() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project Skills Overrides"]));
  wrap.appendChild(el("p", { class: "help-text" }, ["Configure skill overrides specific to this project."]));

  let projData;
  try { projData = await api.get("/api/config/project-skills-registry").catch(() => ({ skills: {} })); }
  catch (err) { projData = { skills: {} }; }
  
  const projSkills = projData.skills || {};
  let dirty = false;
  const markDirty = () => { dirty = true; renderProjList(); };

  const renderSkillPanel = (id, skill) => {
    const p = el("div", { class: "panel", style: "margin-bottom:12px;" });
    const header = el("div", { style: "display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;" });
    header.appendChild(el("h3", { style: "margin:0" }, [id]));
    const delBtn = el("button", { class: "btn btn-danger btn-sm" }, ["Delete"]);
    delBtn.onclick = () => { delete projSkills[id]; markDirty(); };
    header.appendChild(delBtn);
    p.appendChild(header);

    const mkInput = (labelTxt, key, type = "text") => {
      const lbl = el("label", {}, [labelTxt]);
      const inp = el("input", { type, class: "form-control", value: skill[key] || "" });
      inp.oninput = (e) => { skill[key] = e.target.value; markDirty(); };
      p.appendChild(lbl); p.appendChild(inp);
    };
    mkInput("Repo URL", "repo");
    mkInput("Version (Branch/Tag)", "version");
    
    return p;
  };

  const projListContainer = el("div", { style: "margin-bottom:24px" });
  
  const renderProjList = () => {
    projListContainer.innerHTML = "";
    if (Object.keys(projSkills).length === 0) {
      projListContainer.appendChild(el("div", { class: "muted" }, ["No project skill overrides."]));
    } else {
      for (const [id, skill] of Object.entries(projSkills)) {
        projListContainer.appendChild(renderSkillPanel(id, skill));
      }
    }
  };
  
  renderProjList();
  wrap.appendChild(projListContainer);

  const addBtn = el("button", { class: "btn" }, ["+ Add Skill Override"]);
  addBtn.onclick = () => {
    const id = prompt("Skill ID:");
    if (id && !projSkills[id]) {
      projSkills[id] = { repo: "", version: "main" };
      markDirty();
    }
  };
  wrap.appendChild(addBtn);

  const saveBtn = el("button", { class: "btn btn-primary", style: "margin-top:20px; display:block" }, ["Save Overrides"]);
  saveBtn.onclick = async () => {
    try {
      await api.put("/api/config/project-skills-registry", { skills: projSkills });
      toast("Skills overrides saved", "success");
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
content = content.replace('async function viewMcpRegistry() {', overrides_funcs + 'async function viewMcpRegistry() {')

# 6. Routen hinzufügen
old_routes = """  router.register("/project/advanced",        viewProjectAdvanced);
  router.register("/project/gitignore",       viewProjectGitignore);
  router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);"""
new_routes = """  router.register("/project/advanced",        viewProjectAdvanced);
  router.register("/project/gitignore",       viewProjectGitignore);
  router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);
  router.register("/project/mcp-overrides",    viewProjectMcpOverrides);
  router.register("/project/skills-overrides", viewProjectSkillsOverrides);"""
content = content.replace(old_routes, new_routes)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("UI Patched")
