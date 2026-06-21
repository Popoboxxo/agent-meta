import sys

def main():
    with open('docs/admin-ui.html', 'r', encoding='utf-8') as f:
        content = f.read()

    new_func = """async function viewModelDashboard() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Model Discovery & Pricing"]));

  // Global Edit Mode State
  let editMode = false;
  let modelsData = [];
  let aiProvidersData = {};
  let tierPresetsData = {};

  const controls = el("div", { class: "btn-row", style: "margin-bottom: 20px; align-items: center; display: flex; gap: 10px;" });
  
  const refreshBtn = el("button", { class: "btn btn-primary" }, ["Refresh via sync.py"]);
  const saveBtn = el("button", { class: "btn btn-primary", style: "background: var(--accent-green); border-color: var(--accent-green); color: white; display: none;" }, ["Save Configs"]);
  
  const editLabel = el("label", { style: "margin-left: auto; display: flex; align-items: center; gap: 5px; cursor: pointer; user-select: none;" }, [
    el("span", {}, ["Edit Mode"])
  ]);
  const editToggle = el("input", { type: "checkbox" });
  editLabel.prepend(editToggle);
  
  controls.appendChild(refreshBtn);
  controls.appendChild(saveBtn);
  controls.appendChild(editLabel);
  wrap.appendChild(controls);

  const filterState = {
    provider: "",
    model: "",
    category: "",
    inCost: "",
    outCost: "",
    factor: "",
    ref: ""
  };

  const tableWrap = el("div", { id: "models-table-wrap" });
  const providersWrap = el("div", { id: "providers-wrap", style: "margin-top: 30px;" });
  const presetsWrap = el("div", { id: "presets-wrap", style: "margin-top: 30px;" });
  
  wrap.appendChild(tableWrap);
  wrap.appendChild(providersWrap);
  wrap.appendChild(presetsWrap);

  const applyFilters = () => {
    const rows = tableWrap.querySelectorAll("tbody tr");
    rows.forEach(tr => {
      const texts = Array.from(tr.children).map(td => td.textContent.toLowerCase());
      const pMatch = !filterState.provider || texts[0].includes(filterState.provider.toLowerCase());
      const mMatch = !filterState.model || texts[1].includes(filterState.model.toLowerCase());
      const cMatch = !filterState.category || texts[2].includes(filterState.category.toLowerCase());
      
      if (pMatch && mMatch && cMatch) {
        tr.style.display = "";
      } else {
        tr.style.display = "none";
      }
    });
  };

  const createFilterInput = (key) => {
    const input = el("input", { type: "text", placeholder: "Filter...", style: "width: 100%; box-sizing: border-box; margin-top: 4px; font-weight: normal; font-size: 0.9em; padding: 2px 4px;" });
    input.addEventListener("input", (e) => {
      filterState[key] = e.target.value;
      applyFilters();
    });
    return input;
  };

  const renderTable = () => {
    tableWrap.innerHTML = "";
    if (modelsData.length === 0) {
      tableWrap.innerHTML = "<div class='empty'>No models found in registry. Click refresh to discover.</div>";
      return;
    }
    
    const table = el("table", { class: "data", id: "models-table" });
    const thead = el("thead");
    
    // Headers with filters
    thead.appendChild(el("tr", {}, [
      el("th", {}, ["Provider", el("br"), createFilterInput("provider")]),
      el("th", {}, ["Model (Name & ID)", el("br"), createFilterInput("model")]),
      el("th", {}, ["Category", el("br"), createFilterInput("category")]),
      el("th", {}, ["Input Cost ($/1M)"]),
      el("th", {}, ["Output Cost ($/1M)"]),
      el("th", {}, ["Blended $/1M (30/70)"]),
      el("th", {}, ["Actions / Ref"]),
    ]));
    table.appendChild(thead);
    
    const tbody = el("tbody");
    modelsData.forEach(m => {
      const tr = el("tr");
      tr.dataset.provider = m.provider;
      tr.dataset.modelId = m.id;

      tr.appendChild(el("td", {}, [m.provider]));
      tr.appendChild(el("td", {}, [
        el("strong", {}, [m.name || m.id]),
        el("br"),
        el("small", { class: "muted mono" }, [m.id])
      ]));
      tr.appendChild(el("td", {}, [el("span", { class: "badge" }, [m.tier || "Standard"])]));
      
      const inVal = m.input_cost?.toFixed(2) || "0.00";
      const outVal = m.output_cost?.toFixed(2) || "0.00";
      
      // Cost fields container
      const inTd = el("td", { class: "mono" });
      const outTd = el("td", { class: "mono" });
      
      const inInput = el("input", { type: "number", step: "0.01", style: "width: 80px;", value: inVal, class: "cost-input-in" });
      const outInput = el("input", { type: "number", step: "0.01", style: "width: 80px;", value: outVal, class: "cost-input-out" });
      
      const inSpan = el("span", { class: "cost-text" }, [inVal]);
      const outSpan = el("span", { class: "cost-text" }, [outVal]);
      
      inInput.style.display = editMode ? "inline-block" : "none";
      outInput.style.display = editMode ? "inline-block" : "none";
      inSpan.style.display = editMode ? "none" : "inline-block";
      outSpan.style.display = editMode ? "none" : "inline-block";

      const inBadgeClass = (m.input_source === "Overlay") ? "badge warn" : "badge ok";
      const outBadgeClass = (m.output_source === "Overlay") ? "badge warn" : "badge ok";

      inTd.appendChild(inInput);
      inTd.appendChild(inSpan);
      inTd.appendChild(el("span", { class: inBadgeClass, style: "margin-left: 8px;" }, [m.input_source || "API"]));
      
      outTd.appendChild(outInput);
      outTd.appendChild(outSpan);
      outTd.appendChild(el("span", { class: outBadgeClass, style: "margin-left: 8px;" }, [m.output_source || "API"]));
      
      tr.appendChild(inTd);
      tr.appendChild(outTd);
      
      const cf = m.cost_factor || 0;
      let heatColor = "var(--accent-blue)";
      if (cf > 20) heatColor = "var(--accent-yellow)";
      if (cf > 50) heatColor = "var(--accent-red)";
      
      tr.appendChild(el("td", { style: `color: ${heatColor}; font-weight: bold;` }, [
        cf.toFixed(2),
        el("span", { class: "badge optional", style: "margin-left: 8px;" }, ["Calc"])
      ]));
      
      const actionTd = el("td", {});
      if (m.source_url && !editMode) {
        actionTd.appendChild(el("a", { href: m.source_url, target: "_blank" }, ["Pricing URL"]));
      }
      
      const resetBtn = el("button", { class: "btn-icon", style: "cursor: pointer; background: transparent; border: none; font-size: 1.2em;", title: "Reset Pricing Overlay" }, ["🗑️"]);
      resetBtn.style.display = editMode ? "inline-block" : "none";
      resetBtn.onclick = async () => {
        if (!confirm(`Reset pricing overlay for ${m.id}?`)) return;
        const r = await api.post("/api/pricing/reset", { provider: m.provider, id: m.id });
        if (r.success) {
          toast("Pricing reset", "success");
          await loadData();
        } else {
          toast("Reset failed", "error");
        }
      };
      
      actionTd.appendChild(resetBtn);
      
      tr.appendChild(actionTd);
      
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    applyFilters();
  };

  const getDatalistId = (provider) => `dl-${provider.replace(/[^a-zA-Z0-9]/g, '-')}`;

  const renderProviders = () => {
    providersWrap.innerHTML = "";
    providersWrap.appendChild(el("h2", {}, ["Provider Tier Mappings"]));
    providersWrap.appendChild(el("p", { class: "muted" }, ["Map specific models to abstract performance tiers for each provider. Readings from ai-providers.yaml"]));
    
    // Create datalists for each provider's models
    const uniqueProviders = [...new Set(modelsData.map(m => m.provider))];
    uniqueProviders.forEach(p => {
      const dl = el("datalist", { id: getDatalistId(p) });
      modelsData.filter(m => m.provider === p).forEach(m => {
        dl.appendChild(el("option", { value: m.id }, [m.name]));
      });
      providersWrap.appendChild(dl);
    });
    
    const table = el("table", { class: "data provider-tiers-table" });
    const thead = el("thead");
    thead.appendChild(el("tr", {}, [
      el("th", {}, ["Provider"]),
      el("th", {}, ["Tier: nano"]),
      el("th", {}, ["Tier: fast"]),
      el("th", {}, ["Tier: balanced"]),
      el("th", {}, ["Tier: powerful"]),
      el("th", {}, ["Tier: max"]),
    ]));
    table.appendChild(thead);
    
    const tbody = el("tbody");
    
    const providersList = Object.keys(aiProvidersData).length > 0 ? Object.keys(aiProvidersData) : uniqueProviders;
    
    providersList.forEach(p => {
      const tr = el("tr");
      tr.dataset.provider = p;
      tr.appendChild(el("td", {}, [el("strong", {}, [p])]));
      
      const tiers = ["nano", "fast", "balanced", "powerful", "max"];
      const pData = aiProvidersData[p] || {};
      const tData = pData.tiers || {};
      
      tiers.forEach(t => {
        const td = el("td", {});
        const val = tData[t] || "";
        
        if (editMode) {
          const input = el("input", { type: "text", list: getDatalistId(p), value: val, class: `tier-input-${t}`, style: "width: 100%; box-sizing: border-box;" });
          td.appendChild(input);
        } else {
          td.appendChild(el("span", { class: "mono" }, [val || "-"]));
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    providersWrap.appendChild(table);
  };

  const renderPresets = () => {
    presetsWrap.innerHTML = "";
    presetsWrap.appendChild(el("h2", {}, ["Tier Presets"]));
    presetsWrap.appendChild(el("p", { class: "muted" }, ["Manage configuration templates that map generic tasks to required model tiers. (tier-presets.yaml)"]));
    
    const table = el("table", { class: "data tier-presets-table" });
    const thead = el("thead");
    thead.appendChild(el("tr", {}, [
      el("th", {}, ["Preset ID"]),
      el("th", {}, ["Description"]),
      el("th", {}, ["nano"]),
      el("th", {}, ["fast"]),
      el("th", {}, ["balanced"]),
      el("th", {}, ["powerful"]),
      el("th", {}, ["max"])
    ]));
    table.appendChild(thead);
    
    const tbody = el("tbody");
    
    // Convert dict to array to map
    Object.keys(tierPresetsData).forEach(presetId => {
      const tr = el("tr");
      tr.dataset.presetId = presetId;
      const data = tierPresetsData[presetId];
      
      tr.appendChild(el("td", {}, [el("strong", {}, [presetId])]));
      
      if (editMode) {
        tr.appendChild(el("td", {}, [el("input", { type: "text", class: "preset-desc", value: data.description || "", style: "width: 100%; box-sizing: border-box;" })]));
      } else {
        tr.appendChild(el("td", {}, [data.description || "-"]));
      }
      
      const mapping = data.mapping || {};

      ["nano", "fast", "balanced", "powerful", "max"].forEach(tierKey => {
        const td = el("td", {});
        const val = mapping[tierKey] || "";

        if (editMode) {
          const input = el("input", { type: "text", class: `preset-mapping-${tierKey}`, value: val, style: "width: 100%; box-sizing: border-box;" });
          td.appendChild(input);
        } else {
          td.appendChild(el("span", { class: "badge" }, [val || "-"]));
        }
        tr.appendChild(td);
      });
      
      tbody.appendChild(tr);
    });
    
    table.appendChild(tbody);
    presetsWrap.appendChild(table);
  };

  const loadData = async () => {
    try {
      const [resModels, resProviders, resPresets] = await Promise.all([
        api.get("/api/models"),
        api.get("/api/ai-providers"),
        api.get("/api/tier-presets")
      ]);
      
      modelsData = resModels.models || [];
      aiProvidersData = resProviders || {};
      tierPresetsData = resPresets || {};
      
      renderTable();
      renderProviders();
      renderPresets();
    } catch (err) {
      tableWrap.innerHTML = "";
      tableWrap.appendChild(renderError(err));
    }
  };

  editToggle.addEventListener("change", (e) => {
    editMode = e.target.checked;
    saveBtn.style.display = editMode ? "inline-block" : "none";
    
    // Re-render to show/hide inputs
    renderTable();
    renderProviders();
    renderPresets();
  });

  refreshBtn.onclick = async () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Running sync.py...";
    try {
      const r = await api.post("/api/models/update");
      if (r.success) {
        toast("Models updated successfully", "success");
        await loadData();
      } else {
        toast("Model update failed", "error");
      }
    } catch (err) {
      toast("Error: " + err.message, "error");
    } finally {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "Refresh via sync.py";
    }
  };

  saveBtn.onclick = async () => {
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";
    
    try {
      // 1. Collect Pricing Updates
      const pricingUpdates = [];
      tableWrap.querySelectorAll("tr[data-provider]").forEach(tr => {
        const inInput = tr.querySelector(".cost-input-in");
        const outInput = tr.querySelector(".cost-input-out");
        if (inInput && outInput) {
            pricingUpdates.push({
              provider: tr.dataset.provider,
              id: tr.dataset.modelId,
              input_cost: inInput.value ? parseFloat(inInput.value) : 0,
              output_cost: outInput.value ? parseFloat(outInput.value) : 0
            });
        }
      });
      
      // 2. Collect Providers Updates
      const newProvidersData = JSON.parse(JSON.stringify(aiProvidersData));
      providersWrap.querySelectorAll("tr[data-provider]").forEach(tr => {
        const p = tr.dataset.provider;
        if (!newProvidersData[p]) newProvidersData[p] = { tiers: {} };
        if (!newProvidersData[p].tiers) newProvidersData[p].tiers = {};
        
        ["nano", "fast", "balanced", "powerful", "max"].forEach(t => {
          const input = tr.querySelector(`.tier-input-${t}`);
          if (input) {
            if (input.value) newProvidersData[p].tiers[t] = input.value;
            else delete newProvidersData[p].tiers[t];
          }
        });
      });
      
      // 3. Collect Presets Updates
      const newPresetsData = JSON.parse(JSON.stringify(tierPresetsData));
      presetsWrap.querySelectorAll("tr[data-preset-id]").forEach(tr => {
        const pid = tr.dataset.presetId;
        const descInput = tr.querySelector(".preset-desc");
        if (descInput) {
          newPresetsData[pid].description = descInput.value;
        }
        
        if (!newPresetsData[pid].mapping) newPresetsData[pid].mapping = {};

        ["nano", "fast", "balanced", "powerful", "max"].forEach(tierKey => {
          const input = tr.querySelector(`.preset-mapping-${tierKey}`);
          if (input) {
            if (input.value) newPresetsData[pid].mapping[tierKey] = input.value;
            else delete newPresetsData[pid].mapping[tierKey];
          }
        });
      });

      const p1 = api.post("/api/pricing/update", { updates: pricingUpdates });
      const p2 = api.post("/api/ai-providers/update", Object.keys(newProvidersData).length > 0 ? newProvidersData : {});
      const p3 = api.post("/api/tier-presets/update", Object.keys(newPresetsData).length > 0 ? newPresetsData : {});
      
      await Promise.all([p1, p2, p3]);
      
      toast("Configs saved successfully", "success");
      await loadData();
    } catch (err) {
      toast("Error saving: " + err.message, "error");
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save Configs";
    }
  };

  loadData();
  return wrap;
}"""

    idx_start = content.find('async function viewModelDashboard() {')
    idx_end = content.find('/* =========================================================================', idx_start)
    
    if idx_start == -1 or idx_end == -1:
        print("Could not find bounds")
        sys.exit(1)
        
    new_content = content[:idx_start] + new_func + '\n\n' + content[idx_end:]
    
    with open('docs/admin-ui.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("UI Patched Successfully")

if __name__ == '__main__':
    main()
