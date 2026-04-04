from pathlib import Path

from price_tracker.models import BalfourProject, Contractor, MaterialSelection, SelectionStatus, Supplier


def _render_scope_items(items: list, indent: int = 0) -> list[str]:
    """Render scope items as Markdown bullet points.

    Items can be: str, list[str] (sub-bullets), or dict with text/items.
    The JSON pattern is: "Parent Item", ["Sub Item 1", "Sub Item 2"], "Next Parent"
    """
    lines = []
    prefix = "  " * indent + "- "
    for item in items:
        if isinstance(item, str):
            lines.append(f"{prefix}{item}")
        elif isinstance(item, list):
            # Sub-items of the previous parent
            for sub in item:
                if isinstance(sub, str):
                    lines.append(f"  {prefix}{sub}")
                elif isinstance(sub, list):
                    lines.extend(_render_scope_items(sub, indent + 2))
        elif isinstance(item, dict):
            if "text" in item:
                lines.append(f"{prefix}{item['text']}")
            if "items" in item:
                lines.extend(_render_scope_items(item["items"], indent + 1))
    return lines


def _render_contractor(contractor: Contractor, project: BalfourProject) -> str:
    """Render a contractor README.md."""
    lines = [f"# {contractor.name}", ""]

    if contractor.related_suppliers:
        supplier_links = []
        for sid in contractor.related_suppliers:
            sup = next((s for s in project.suppliers if s.id == sid), None)
            name = sup.name if sup else sid.replace("-", " ").title()
            supplier_links.append(f"[{name}](../../suppliers/{sid})")
        lines.append(f"**Related Suppliers:** {', '.join(supplier_links)}")
        lines.append("")

    if contractor.warranty:
        lines.append(f"- {contractor.warranty}")
        lines.append("")

    for section in contractor.scope:
        if section.section:
            lines.append(f"## {section.section}")
            lines.append("")
        lines.extend(_render_scope_items(section.items))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_selection_table(selections: list[MaterialSelection]) -> list[str]:
    """Render material selections as a Markdown table."""
    if not selections:
        return []

    lines = [
        "## Material Selections",
        "",
        "| Item | Brand | Model | Color | Status | Unit Price | Qty | Total | Last Validated |",
        "|------|-------|-------|-------|--------|-----------|-----|-------|----------------|",
    ]

    for sel in selections:
        status_display = sel.status.value.replace("_", " ").title()
        brand = sel.brand or "—"
        model = sel.model or "—"
        color = sel.color or "—"
        price = f"${sel.unit_price:,.2f}/{sel.unit}" if sel.unit_price else "—"
        qty = f"{sel.quantity:,.0f}" if sel.quantity else "—"
        total = f"${sel.total_with_tax:,.2f}" if sel.total_with_tax else "—"
        validated = sel.price_validated_date or "—"

        lines.append(f"| {sel.item_name} | {brand} | {model} | {color} | {status_display} | {price} | {qty} | {total} | {validated} |")

    lines.append("")
    return lines


def _render_supplier(supplier: Supplier, project: BalfourProject) -> str:
    """Render a supplier README.md with material selections."""
    lines = [f"# {supplier.name}", ""]

    if supplier.related_contractors:
        contractor_links = []
        for cid in supplier.related_contractors:
            con = next((c for c in project.contractors if c.id == cid), None)
            name = con.name if con else cid.replace("-", " ").title()
            contractor_links.append(f"[{name}](../../contractors/{cid})")
        lines.append(f"**Related Contractors:** {', '.join(contractor_links)}")
        lines.append("")

    for section in supplier.materials:
        if section.section:
            lines.append(f"## {section.section}")
            lines.append("")
        lines.extend(_render_scope_items(section.items))
        lines.append("")

    lines.extend(_render_selection_table(supplier.selections))

    return "\n".join(lines).rstrip() + "\n"


def _render_contractors_suppliers_index(project: BalfourProject) -> str:
    """Render the contractors-and-suppliers/README.md index."""
    lines = ["# Contractors and Suppliers", ""]

    lines.append("## Contractors")
    lines.append("")
    for c in sorted(project.contractors, key=lambda x: x.name):
        lines.append(f"- [{c.name}](contractors/{c.id})")
    lines.append("")

    lines.append("## Suppliers")
    lines.append("")
    for s in sorted(project.suppliers, key=lambda x: x.name):
        lines.append(f"- [{s.name}](suppliers/{s.id})")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_project_readme(project: BalfourProject) -> str:
    """Render the top-level balfour/README.md."""
    lines = [
        f"# {project.project.name}",
        "",
        f"**Status:** {project.project.status.replace('_', ' ').title()}",
        f"**Last Updated:** {project.project.last_updated}",
        "",
        "## Documentation",
        "",
        "- [Suppliers and Contractors Spec](docs/suppliers-and-contractors.md)",
        "- [Decisions / Todo Checklist](docs/decisions-todo-checklist.md)",
        "- [Quotes Checklist](docs/quotes-checklist.md)",
        "- [Material Takeoff Briefing](docs/material-takeoff-briefing.md)",
        "- [Material Takeoff Checklist](docs/material-takeoff-checklist.md)",
        "",
        "## Contractors and Suppliers",
        "",
        "- [All Contractors and Suppliers](contractors-and-suppliers)",
        "",
        "## Reference Documents",
        "",
        "- [House Plans and Engineering](reference-docs)",
        "",
        "## Construction Phases",
        "",
    ]
    for phase in sorted(project.phases, key=lambda p: p.order):
        lines.append(f"- {phase.name}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_decisions(project: BalfourProject) -> str:
    """Render decisions-todo-checklist.md."""
    lines = ["# Decisions / Todo Checklist", ""]

    by_category: dict[str, list] = {}
    for d in project.decisions:
        by_category.setdefault(d.category, []).append(d)

    for cat in sorted(by_category):
        lines.append(f"## {cat}")
        lines.append("")
        for d in by_category[cat]:
            status = "x" if d.status.value == "resolved" else " "
            resolved = f" → {d.resolved_value}" if d.resolved_value else ""
            lines.append(f"- [{status}] {d.description}{resolved}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_quotes(project: BalfourProject) -> str:
    """Render quotes-checklist.md."""
    lines = ["# Quotes Checklist", ""]

    lines.append("## Contractors")
    lines.append("")
    lines.append("| Contractor | Phase | Status | Amount |")
    lines.append("|-----------|-------|--------|--------|")
    for c in project.contractors:
        status = c.quote.status.value.replace("_", " ").title()
        amount = f"${c.quote.amount:,.2f}" if c.quote.amount else "—"
        phase = c.phase.replace("_", " ").title()
        lines.append(f"| {c.name} | {phase} | {status} | {amount} |")
    lines.append("")

    lines.append("## Suppliers")
    lines.append("")

    needs_count = 0
    selected_count = 0
    for s in project.suppliers:
        for sel in s.selections:
            if sel.status == SelectionStatus.NEEDS_SELECTION:
                needs_count += 1
            else:
                selected_count += 1

    lines.append(f"**Selections:** {selected_count} made, {needs_count} remaining")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_reference_docs(project: BalfourProject) -> str:
    """Render reference-docs/README.md."""
    lines = ["# Reference Documents", ""]

    if project.reference_docs.house_plans:
        lines.append("## House Plans")
        lines.append("")
        for doc in project.reference_docs.house_plans:
            lines.append(f"- [{doc.name}](house-plans/{doc.filename})")
        lines.append("")

    if project.reference_docs.civil_engineer:
        lines.append("## Civil Engineer")
        lines.append("")
        for doc in project.reference_docs.civil_engineer:
            lines.append(f"- [{doc.name}](civil-engineer/{doc.filename})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_master_spec(project: BalfourProject) -> str:
    """Render suppliers-and-contractors.md — the master spec with all contractors and suppliers inline."""
    # Use raw markdown if available
    import json as _json
    _data_file = Path(__file__).resolve().parents[3] / "balfour" / "data" / "balfour.json"
    with open(_data_file) as _f:
        _raw_data = _json.load(_f)
    raw = _raw_data.get("master_spec_raw_markdown")
    if raw:
        return raw

    lines = ["# Balfour Home Suppliers and Contractors", "", "---", ""]

    # Table of contents
    lines.append("# Table of Contents")
    lines.append("")
    lines.append("## Contractors")
    lines.append("")
    for c in project.contractors:
        anchor = c.name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        lines.append(f"- [{c.name}](#{anchor})")
    lines.append("")
    lines.append("## Suppliers")
    lines.append("")
    for s in project.suppliers:
        anchor = s.name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "").replace("  ", " ").replace(" ", "-")
        lines.append(f"- [{s.name}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Contractor sections
    lines.append("# Contractors")
    lines.append("")
    for c in project.contractors:
        lines.append(f"## {c.name}")
        lines.append("")
        if c.related_suppliers:
            supplier_names = []
            for sid in c.related_suppliers:
                sup = next((s for s in project.suppliers if s.id == sid), None)
                name = sup.name if sup else sid.replace("-", " ").title()
                anchor = name.lower().replace(" ", "-").replace("&", "").replace("  ", " ").replace(" ", "-")
                supplier_names.append(f"[{name}](#{anchor})")
            lines.append(f"**Related Suppliers:** {', '.join(supplier_names)}")
            lines.append("")
        if c.warranty:
            lines.append(f"- {c.warranty}")
            lines.append("")
        for section in c.scope:
            if section.section:
                lines.append(f"### {section.section}")
                lines.append("")
            lines.extend(_render_scope_items(section.items))
            lines.append("")
        lines.append("---")
        lines.append("")

    # Supplier sections
    lines.append("# Suppliers")
    lines.append("")
    for s in project.suppliers:
        lines.append(f"## {s.name}")
        lines.append("")
        if s.related_contractors:
            contractor_names = []
            for cid in s.related_contractors:
                con = next((c for c in project.contractors if c.id == cid), None)
                name = con.name if con else cid.replace("-", " ").title()
                anchor = name.lower().replace(" ", "-").replace("(", "").replace(")", "")
                contractor_names.append(f"[{name}](#{anchor})")
            lines.append(f"**Related Contractors:** {', '.join(contractor_names)}")
            lines.append("")
        for section in s.materials:
            if section.section:
                lines.append(f"### {section.section}")
                lines.append("")
            lines.extend(_render_scope_items(section.items))
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_specs(specs, indent: int = 0) -> list[str]:
    """Render specification data in any format the JSON uses."""
    lines = []
    prefix = "  " * indent

    if specs is None:
        return lines
    elif isinstance(specs, str):
        lines.append(f"{prefix}- {specs}")
    elif isinstance(specs, list):
        for item in specs:
            if isinstance(item, str):
                lines.append(f"{prefix}- {item}")
            elif isinstance(item, dict):
                # Could be a table row (location/psi/etc) or a subsection
                if "table" in item:
                    table = item["table"]
                    if table.get("headers"):
                        lines.append("")
                        lines.append(f"{prefix}| " + " | ".join(table["headers"]) + " |")
                        lines.append(f"{prefix}|" + "|".join(["---"] * len(table["headers"])) + "|")
                    for row in table.get("rows", []):
                        lines.append(f"{prefix}| " + " | ".join(str(c) for c in row) + " |")
                    lines.append("")
                elif "location" in item:
                    # Concrete-style spec row
                    parts = [f"{k}: {v}" for k, v in item.items()]
                    lines.append(f"{prefix}- {', '.join(parts)}")
                elif "surface" in item:
                    # Paint-style spec row
                    surface = item.get("surface", "")
                    product = item.get("product", "")
                    sheen = item.get("sheen", "")
                    lines.append(f"{prefix}| {surface} | {product} | {sheen} |")
                elif "note" in item:
                    lines.append("")
                    lines.append(f"{prefix}**{item.get('label', 'Note')}:**")
                    for n in item.get("note", []):
                        lines.append(f"{prefix}- {n}")
                else:
                    # Generic dict — render key: value pairs
                    for k, v in item.items():
                        if isinstance(v, list):
                            lines.append(f"{prefix}- {k}:")
                            for sub in v:
                                lines.append(f"{prefix}  - {sub}")
                        else:
                            lines.append(f"{prefix}- {k}: {v}")
            elif isinstance(item, list):
                for sub in item:
                    lines.append(f"{prefix}  - {sub}")
    elif isinstance(specs, dict):
        for key, value in specs.items():
            label = key.replace("_", " ").title()
            if isinstance(value, str):
                lines.append(f"{prefix}- {label}: {value}")
            elif isinstance(value, list):
                lines.append(f"{prefix}**{label}:**")
                for item in value:
                    if isinstance(item, str):
                        lines.append(f"{prefix}- {item}")
                    elif isinstance(item, dict):
                        if "surface" in item:
                            # Paint table row
                            if not any("Surface" in l for l in lines):
                                lines.append(f"{prefix}")
                                lines.append(f"{prefix}| Surface | Product | Sheen |")
                                lines.append(f"{prefix}|---------|---------|-------|")
                            lines.append(f"{prefix}| {item.get('surface','')} | {item.get('product','')} | {item.get('sheen','')} |")
                        else:
                            parts = [f"{k}: {v}" for k, v in item.items()]
                            lines.append(f"{prefix}- {', '.join(parts)}")
                lines.append("")
            elif isinstance(value, dict):
                lines.append(f"{prefix}**{label}:**")
                lines.extend(_render_specs(value, indent + 1))
                lines.append("")

    return lines


def _render_material_takeoff_briefing(project: BalfourProject) -> str:
    """Render material-takeoff-briefing.md from JSON data."""
    mt = project.material_takeoff
    if not mt or not mt.briefing:
        return "# Balfour Home - Material Takeoff Briefing\n\nNo briefing data available.\n"

    b = mt.briefing

    # Use raw markdown if available (preserves exact original formatting)
    if isinstance(b, dict) and b.get("raw_markdown"):
        return b["raw_markdown"]

    phase_display = {
        "phase_1_site_work": "Phase 1: Site Work",
        "phase_2_foundation": "Phase 2: Foundation",
        "phase_3_framing": "Phase 3: Framing",
        "phase_4_dry_in": "Phase 4: Dry-In",
        "phase_5_rough_interior": "Phase 5: Rough Interior",
        "phase_6_finishes": "Phase 6: Finishes",
        "phase_7_site_finish": "Phase 7: Site Finish",
    }

    lines = [
        "# Balfour Home - Material Takeoff Briefing",
        "",
        f"**Project:** {b.get('project', 'Balfour Home')}",
        f"**Version:** {b.get('version', '1.0')}",
        "**Date:** _______________",
        "**Contact:** _______________",
        "",
        "---",
        "",
    ]

    # TOC
    lines.append("# Table of Contents")
    lines.append("")
    lines.append("- [Documents Provided](#documents-provided)")
    lines.append("- [Deliverable Requirements](#deliverable-requirements)")
    lines.append("- [Excluded Categories](#excluded-categories)")
    lines.append("- [Material Specifications](#material-specifications)")
    phases = b.get("phases", {})
    for phase_key, phase_data in phases.items():
        phase_name = phase_display.get(phase_key, phase_key.replace("_", " ").title())
        anchor = phase_name.lower().replace(" ", "-").replace(":", "")
        lines.append(f"  - [{phase_name}](#{anchor})")
        for cat_key in phase_data:
            if isinstance(phase_data[cat_key], dict):
                cat_name = cat_key.replace("_", " ").title()
                cat_anchor = cat_name.lower().replace(" ", "-")
                lines.append(f"    - [{cat_name}](#{cat_anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Documents provided
    docs = b.get("documents_provided", [])
    if docs:
        lines.append("# Documents Provided")
        lines.append("")
        lines.append("The following documents are available for scaling and quantity calculations:")
        lines.append("")
        lines.append("| Document | Link | Description |")
        lines.append("|----------|------|-------------|")
        for doc in docs:
            name = doc.get("name", "")
            filename = doc.get("filename", "").replace(" ", "%20")
            desc = doc.get("description", "")
            folder = "house-plans"
            if "survey" in name.lower() or "topo" in name.lower() or "plot" in name.lower():
                folder = "civil-engineer"
            lines.append(f"| {name} | [Download](../reference-docs/{folder}/{filename}) | {desc} |")
        lines.append("")

    # Pending documents
    pending = b.get("pending_documents", [])
    if pending:
        lines.append("**Pending Documents (will be added when available):**")
        lines.append("")
        for doc in pending:
            lines.append(f"- {doc}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Deliverable requirements
    dreqs = b.get("deliverable_requirements", {})
    if dreqs:
        lines.append("# Deliverable Requirements")
        lines.append("")

        fmt_reqs = dreqs.get("format", [])
        if fmt_reqs:
            lines.append("## Format Requirements")
            lines.append("")
            lines.append("| Requirement | Description |")
            lines.append("|-------------|-------------|")
            for req in fmt_reqs:
                lines.append(f"| {req.get('requirement', '')} | {req.get('description', '')} |")
            lines.append("")

        phases_table = dreqs.get("phasing", [])
        if phases_table:
            lines.append("## Phasing/Ordering Sequence")
            lines.append("")
            lines.append("Organize materials by construction phase for staged ordering:")
            lines.append("")
            lines.append("| Phase | Description | Categories |")
            lines.append("|-------|-------------|------------|")
            for p in phases_table:
                lines.append(f"| {p.get('phase', '')} | {p.get('description', '')} | {p.get('categories', '')} |")
            lines.append("")

        sru = dreqs.get("summary_rollup_sheet")
        if sru:
            lines.append("## Summary Roll-Up Sheet")
            lines.append("")
            lines.append(sru)
            lines.append("")

        fvl = dreqs.get("field_verification_list")
        if fvl:
            lines.append("## Field Verification List")
            lines.append("")
            lines.append(fvl)
            lines.append("")

        waste = dreqs.get("waste_factor_guidelines", [])
        if waste:
            lines.append("## Waste Factor Guidelines")
            lines.append("")
            lines.append("Apply and document waste percentages. Suggested factors (or propose your standard):")
            lines.append("")
            lines.append("| Material | Suggested Waste % |")
            lines.append("|----------|-------------------|")
            for w in waste:
                pct = w.get("suggested_waste_percent", w.get("waste_pct", ""))
                lines.append(f"| {w.get('material', '')} | {pct}% |")
            lines.append("")

        expected = dreqs.get("expected_line_items", [])
        if expected:
            lines.append("## Expected Line Items by Category")
            lines.append("")
            lines.append("| Category | Line Items Required |")
            lines.append("|----------|---------------------|")
            for e in expected:
                lines.append(f"| {e.get('category', '')} | {e.get('line_items', '')} |")
            lines.append("")

    lines.append("---")
    lines.append("")

    # Excluded categories
    excluded = b.get("excluded_categories", [])
    if excluded:
        lines.append("# Excluded Categories")
        lines.append("")
        lines.append("**DO NOT include quantities for the following - they are handled separately:**")
        lines.append("")
        for cat in excluded:
            lines.append(f"- {cat}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Phases with specs
    phases = b.get("phases", {})
    if phases:
        lines.append("# Material Specifications")
        lines.append("")
        for phase_key, phase_data in phases.items():
            phase_name = phase_display.get(phase_key, phase_key.replace("_", " ").title())
            lines.append(f"## {phase_name}")
            lines.append("")
            # Category display names (preserve original casing)
            cat_display = {
                "silt_fence": "Silt Fence",
                "stone_and_aggregate": "Stone and Aggregate",
                "french_drain": "French Drain",
                "concrete": "Concrete",
                "masonry": "Masonry",
                "lumber_and_framing": "Lumber and Framing",
                "deck": "Deck",
                "steel": "Steel",
                "roofing": "Roofing",
                "windows": "Windows",
                "doors": "Doors",
                "siding": "Siding",
                "gutters_and_downspouts": "Gutters and Downspouts",
                "garage_doors": "Garage Doors",
                "drywall": "Drywall",
                "insulation": "Insulation",
                "carpet": "Carpet",
                "hardwood_flooring": "Hardwood Flooring",
                "tile_and_slate": "Tile and Slate",
                "glass": "Glass",
                "trim_and_molding": "Trim and Molding",
                "paint_and_stain": "Paint and Stain",
                "landscaping": "Landscaping",
            }

            # Categories are direct keys on the phase dict
            for cat_key, cat_data in phase_data.items():
                if not isinstance(cat_data, dict):
                    continue
                cat_name = cat_display.get(cat_key, cat_key.replace("_", " ").title())
                lines.append(f"### {cat_name}")
                lines.append("")
                expected_items = cat_data.get("expected_line_items", [])
                if expected_items:
                    lines.append("**Expected Line Items:**")
                    for item in expected_items:
                        lines.append(f"- [ ] {item}")
                    lines.append("")
                specs = cat_data.get("specifications")
                if specs is not None:
                    lines.append("**Specifications:**")
                    lines.extend(_render_specs(specs))
                    lines.append("")
                lines.append("---")
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _render_material_takeoff_checklist(project: BalfourProject) -> str:
    """Render material-takeoff-checklist.md from JSON data."""
    mt = project.material_takeoff
    if not mt or not mt.checklist:
        return "# Balfour Home - Material Takeoff Validation Checklist\n\nNo checklist data available.\n"

    c = mt.checklist

    # Use raw markdown if available
    if isinstance(c, dict) and c.get("raw_markdown"):
        return c["raw_markdown"]

    lines = [
        "# Balfour Home - Material Takeoff Validation Checklist",
        "",
        f"**Project:** {c.get('project', 'Balfour Home')}",
        "**Estimator:** _______________",
        "**Date Received:** _______________",
        "**Date Reviewed:** _______________",
        "",
        "---",
        "",
    ]

    # Deliverable format verification
    fmt_items = c.get("deliverable_format_verification", [])
    if fmt_items:
        lines.append("# Deliverable Format Verification")
        lines.append("")
        for item in fmt_items:
            lines.append(f"- [ ] {item}")
        lines.append("")
        lines.append("**Format Notes:** _________________________________________________________________")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Phases
    phases = c.get("phases", {})
    if phases:
        lines.append("# Category Checklists")
        lines.append("")
        phase_names = {
            "phase_1_site_work": "Phase 1: Site Work",
            "phase_2_foundation": "Phase 2: Foundation",
            "phase_3_framing": "Phase 3: Framing",
            "phase_4_dry_in": "Phase 4: Dry-In",
            "phase_5_rough_interior": "Phase 5: Rough Interior",
            "phase_6_finishes": "Phase 6: Finishes",
            "phase_7_site_finish": "Phase 7: Site Finish",
        }
        for phase_key, categories in phases.items():
            phase_name = phase_names.get(phase_key, phase_key.replace("_", " ").title())
            lines.append(f"## {phase_name}")
            lines.append("")
            for cat_key, items in categories.items():
                cat_name = cat_key.replace("_", " ").title()
                lines.append(f"### {cat_name}")
                lines.append("")
                for item in items:
                    lines.append(f"- [ ] {item}")
                lines.append("")
                lines.append("**Notes:** _________________________________________________________________")
                lines.append("")
                lines.append("---")
                lines.append("")

    # Sign-off
    sign_off = c.get("sign_off", {})
    if sign_off:
        lines.append("# Sign-Off")
        lines.append("")
        for key, value in sign_off.items():
            label = key.replace("_", " ").title()
            lines.append(f"**{label}:** {value}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_all(project: BalfourProject, repo_root: Path) -> None:
    """Render all Markdown files from the JSON source of truth."""
    balfour = repo_root / "balfour"

    # Project README
    (balfour / "README.md").write_text(_render_project_readme(project))

    # Contractors & suppliers index
    cs_dir = balfour / "contractors-and-suppliers"
    (cs_dir / "README.md").write_text(_render_contractors_suppliers_index(project))

    # Individual contractor pages
    for contractor in project.contractors:
        cdir = cs_dir / "contractors" / contractor.id
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "README.md").write_text(_render_contractor(contractor, project))

    # Individual supplier pages
    for supplier in project.suppliers:
        sdir = cs_dir / "suppliers" / supplier.id
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "README.md").write_text(_render_supplier(supplier, project))

    # Docs
    docs = balfour / "docs"
    (docs / "suppliers-and-contractors.md").write_text(_render_master_spec(project))
    (docs / "decisions-todo-checklist.md").write_text(_render_decisions(project))
    (docs / "quotes-checklist.md").write_text(_render_quotes(project))
    (docs / "material-takeoff-briefing.md").write_text(_render_material_takeoff_briefing(project))
    (docs / "material-takeoff-checklist.md").write_text(_render_material_takeoff_checklist(project))

    # Reference docs
    (balfour / "reference-docs" / "README.md").write_text(_render_reference_docs(project))
