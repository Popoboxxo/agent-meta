import re

with open("docs/ui/admin-ui.html", "r", encoding="utf-8") as f:
    content = f.read()

# I need to find the renderSrvPanel function inside viewProjectMcpOverrides and insert the hints.
# Specifically, between the header and the detailsWrap.

old_header_end = """    toggleBox.appendChild(activeCb);
    header.appendChild(toggleBox);
    p.appendChild(header);

    const detailsWrap = el("div", { style: "margin-top: 12px; display: flex; gap: 12px; flex-direction: column;" });"""

new_header_end = """    toggleBox.appendChild(activeCb);
    header.appendChild(toggleBox);
    p.appendChild(header);

    // --- HINTS / INFO BOX ---
    if (merged.description || (merged.secrets && merged.secrets.length > 0)) {
        const infoBox = el("div", { style: "margin-top: 12px; padding: 8px 12px; background-color: var(--bg-card); border-left: 3px solid #3b82f6; font-size: 12px; color: var(--text-muted); border-radius: 4px;" });
        
        if (merged.description) {
            infoBox.appendChild(el("div", { style: "margin-bottom: 4px;" }, [
                el("strong", { style: "color: var(--text);" }, ["Description: "]), 
                merged.description
            ]));
        }
        
        if (merged.secrets && merged.secrets.length > 0) {
            const secWrap = el("div", {}, [
                el("strong", { style: "color: var(--text);" }, ["Required Environment Variables: "]),
                "Define these locally on your system, or overwrite their {{Placeholders}} in the Customize menu: "
            ]);
            merged.secrets.forEach(sec => {
                const code = el("code", { style: "background: var(--bg-body); padding: 2px 4px; border-radius: 3px; margin-right: 4px; color: #f59e0b;" }, [sec]);
                secWrap.appendChild(code);
            });
            infoBox.appendChild(secWrap);
        }
        
        p.appendChild(infoBox);
    }
    // ------------------------

    const detailsWrap = el("div", { style: "margin-top: 12px; display: flex; gap: 12px; flex-direction: column;" });"""

content = content.replace(old_header_end, new_header_end)

with open("docs/ui/admin-ui.html", "w", encoding="utf-8") as f:
    f.write(content)
print("MCP Hints injected into UI.")
