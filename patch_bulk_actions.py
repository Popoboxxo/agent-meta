import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# I need to find the place where the details list is created in viewProjectGitignore:
# const list = el("div", { style: "margin-top:12px; display:flex; flex-direction:column; gap:12px;" });

old_list_creation = """    const list = el("div", { style: "margin-top:12px; display:flex; flex-direction:column; gap:12px;" });"""

new_list_creation = """    const bulkActions = el("div", { style: "display:flex; justify-content:flex-end; gap:8px; padding-bottom:8px; border-bottom: 1px solid var(--border); margin-bottom: 8px;" });
    const bulkIgnore = el("button", { class: "btn btn-sm" }, ["Set All to IGNORED"]);
    const bulkTrack = el("button", { class: "btn btn-sm" }, ["Set All to TRACKED"]);
    bulkIgnore.onclick = () => { childrenToggles.forEach(ct => ct.setValue(true)); parentToggle.setValue(true); };
    bulkTrack.onclick = () => { childrenToggles.forEach(ct => ct.setValue(false)); parentToggle.setValue(false); };
    bulkActions.appendChild(bulkIgnore);
    bulkActions.appendChild(bulkTrack);
    details.appendChild(bulkActions);

    const list = el("div", { style: "margin-top:12px; display:flex; flex-direction:column; gap:12px;" });"""

if old_list_creation in content:
    content = content.replace(old_list_creation, new_list_creation)
    with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("Bulk actions injected.")
else:
    print("Could not find list creation line.")
