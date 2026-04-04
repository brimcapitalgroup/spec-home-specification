from collections import defaultdict

from rich.console import Console
from rich.table import Table

from price_tracker.models import BalfourProject, SelectionStatus

console = Console()


def report_needs(project: BalfourProject) -> None:
    table = Table(title="Material Selections Needed", show_lines=True)
    table.add_column("Supplier", style="cyan")
    table.add_column("Item", style="white")
    table.add_column("Description", style="dim")
    table.add_column("Unit", style="dim")

    count = 0
    for supplier in sorted(project.suppliers, key=lambda s: s.name):
        for sel in supplier.selections:
            if sel.status == SelectionStatus.NEEDS_SELECTION:
                table.add_row(supplier.name, sel.item_name, sel.description, sel.unit)
                count += 1

    console.print(table)
    console.print(f"\n[bold]{count}[/bold] selections still needed")


def report_totals(project: BalfourProject) -> None:
    table = Table(title="Material Cost Summary", show_lines=True)
    table.add_column("Supplier", style="cyan")
    table.add_column("Items", justify="right")
    table.add_column("Subtotal", justify="right", style="green")
    table.add_column("Tax", justify="right", style="yellow")
    table.add_column("Total", justify="right", style="bold green")

    grand_subtotal = 0.0
    grand_tax = 0.0
    grand_total = 0.0

    for supplier in sorted(project.suppliers, key=lambda s: s.name):
        sub = sum(s.subtotal or 0 for s in supplier.selections)
        tax = sum(s.tax_amount or 0 for s in supplier.selections)
        total = sum(s.total_with_tax or 0 for s in supplier.selections)
        item_count = len([s for s in supplier.selections if s.status != SelectionStatus.NEEDS_SELECTION])

        if supplier.selections:
            table.add_row(
                supplier.name,
                str(item_count),
                f"${sub:,.2f}" if sub else "—",
                f"${tax:,.2f}" if tax else "—",
                f"${total:,.2f}" if total else "—",
            )
            grand_subtotal += sub
            grand_tax += tax
            grand_total += total

    table.add_section()
    table.add_row(
        "[bold]GRAND TOTAL[/bold]",
        "",
        f"[bold]${grand_subtotal:,.2f}[/bold]",
        f"[bold]${grand_tax:,.2f}[/bold]",
        f"[bold]${grand_total:,.2f}[/bold]",
    )

    console.print(table)


def report_status(project: BalfourProject) -> None:
    table = Table(title="Material Selection Status", show_lines=True)
    table.add_column("Supplier", style="cyan")
    table.add_column("Item", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Price Status", style="dim")
    table.add_column("Last Validated", style="dim")
    table.add_column("Unit Price", justify="right")
    table.add_column("Total", justify="right", style="green")

    status_colors = {
        "needs_selection": "red",
        "selected": "yellow",
        "ordered": "blue",
        "delivered": "cyan",
        "installed": "green",
        "unavailable": "red bold",
        "discontinued": "red bold",
    }

    for supplier in sorted(project.suppliers, key=lambda s: s.name):
        for sel in supplier.selections:
            color = status_colors.get(sel.status.value, "white")
            table.add_row(
                supplier.name,
                sel.item_name,
                f"[{color}]{sel.status.value.replace('_', ' ').title()}[/{color}]",
                sel.price_fetch_status.value.replace("_", " ").title(),
                sel.price_validated_date or "—",
                f"${sel.unit_price:,.2f}/{sel.unit}" if sel.unit_price else "—",
                f"${sel.total_with_tax:,.2f}" if sel.total_with_tax else "—",
            )

    console.print(table)
