"""Abstract base class for SE export adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SEAdapter(ABC):
    """Abstract base for all SE export adapters.

    Each concrete adapter maps the internal SE decomposition graph onto an
    external representation (Markdown files, GitHub Issues, Jira, etc.).
    """

    @abstractmethod
    def create_requirement(
        self,
        req_id: str,
        title: str,
        description: str,
        parent_id: str | None = None,
    ) -> str:
        """Create a requirement in the target system.

        Args:
            req_id: Internal requirement identifier (e.g. REQ-L1-SH-001).
            title: Short human-readable title.
            description: Full requirement description.
            parent_id: Optional parent requirement ID for hierarchy.

        Returns:
            External identifier assigned by the target system (e.g. a file
            path, an issue URL, or a ticket key).
        """

    @abstractmethod
    def link_requirements(
        self,
        source_id: str,
        target_id: str,
        link_type: str,
    ) -> None:
        """Link two requirements with a typed relationship.

        Args:
            source_id: External ID of the source requirement.
            target_id: External ID of the target requirement.
            link_type: Relationship type, e.g. "refines" or "verifies".
        """

    @abstractmethod
    def update_status(self, req_id: str, status: str) -> None:
        """Update the lifecycle status of a requirement.

        Args:
            req_id: External identifier of the requirement.
            status: One of draft | approved | implemented | verified.
        """

    @abstractmethod
    def export_interface(self, interface: dict) -> str:
        """Export a CQRS interface contract to the target system.

        Args:
            interface: Interface dict with keys source_id, target_id,
                       interface_type, data_payload (from the schema).

        Returns:
            External identifier for the created interface artefact.
        """

    # ------------------------------------------------------------------
    # Orchestration: export an entire SE decomposition graph
    # ------------------------------------------------------------------

    def export_graph(self, graph: dict) -> dict:
        """Orchestrate a full SE decomposition graph export.

        Iterates the graph in layer order (L1 → L2 subsystems → L3
        components → interfaces), calls create/link/status on each
        node and returns a mapping of internal req_id → external ID.

        Args:
            graph: A dict conforming to schemas/se-decomposition.schema.json.

        Returns:
            Mapping of internal req_id → external ID returned by the
            concrete adapter's create_requirement implementation.
        """
        id_map: dict[str, str] = {}

        feature_id: str = graph.get("feature_id", "REQ-UNKNOWN")
        stakeholder_req: str = graph.get("stakeholder_requirement", "")

        # --- L1: system level ---
        l1 = graph.get("l1_system", {})
        l1_description = l1.get("blackbox", "")
        l1_ext_id = self.create_requirement(
            req_id=feature_id,
            title=f"[L1] {feature_id}",
            description=f"{stakeholder_req}\n\n{l1_description}".strip(),
            parent_id=graph.get("parent_req_id"),
        )
        id_map[feature_id] = l1_ext_id
        self.update_status(l1_ext_id, "draft")

        # --- L2: subsystems ---
        for subsystem in graph.get("l2_subsystems", []):
            sub_id: str = subsystem.get("subsystem_id", "")
            if not sub_id:
                continue
            sub_desc = subsystem.get("blackbox", "")
            sub_ext_id = self.create_requirement(
                req_id=sub_id,
                title=f"[L2] {sub_id}",
                description=sub_desc,
                parent_id=l1_ext_id,
            )
            id_map[sub_id] = sub_ext_id
            self.update_status(sub_ext_id, "draft")
            self.link_requirements(l1_ext_id, sub_ext_id, "refines")

        # --- L3: components ---
        for component in graph.get("l3_components", []):
            comp_id: str = component.get("component_id", "")
            if not comp_id:
                continue
            comp_desc = component.get("description", "")
            parent_sub_id: str | None = component.get("refines")
            parent_ext_id = id_map.get(parent_sub_id) if parent_sub_id else l1_ext_id
            comp_ext_id = self.create_requirement(
                req_id=comp_id,
                title=f"[L3] {comp_id}",
                description=comp_desc,
                parent_id=parent_ext_id,
            )
            id_map[comp_id] = comp_ext_id
            self.update_status(comp_ext_id, "draft")
            if parent_ext_id:
                self.link_requirements(parent_ext_id, comp_ext_id, "refines")

        # --- CQRS interfaces ---
        cqrs = graph.get("cqrs_interfaces", {})
        all_interfaces: list[dict] = (
            cqrs.get("commands", [])
            + cqrs.get("events", [])
            + cqrs.get("queries", [])
        )
        for iface in all_interfaces:
            ext_id = self.export_interface(iface)
            iface_name: str = iface.get("name", "")
            if iface_name and ext_id:
                id_map[iface_name] = ext_id

        # --- sub_components (recursive cell outputs) ---
        for sub_comp in graph.get("sub_components", []):
            sc_id: str = sub_comp.get("id", "")
            if not sc_id:
                continue
            sc_name = sub_comp.get("name", sc_id)
            sc_desc = sub_comp.get("black_box_requirement", "")
            sc_ext_id = self.create_requirement(
                req_id=sc_id,
                title=f"[Component] {sc_name}",
                description=sc_desc,
                parent_id=l1_ext_id,
            )
            id_map[sc_id] = sc_ext_id
            self.update_status(sc_ext_id, "draft")
            self.link_requirements(l1_ext_id, sc_ext_id, "refines")

        return id_map
