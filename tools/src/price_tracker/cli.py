import argparse
import json
import sys
from pathlib import Path

from price_tracker.fetcher import fetch_prices, validate_urls
from price_tracker.models import BalfourProject
from price_tracker.renderer import render_all
from price_tracker.report import report_needs, report_status, report_totals

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_FILE = REPO_ROOT / "balfour" / "data" / "balfour.json"


def load_project() -> BalfourProject:
    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} not found", file=sys.stderr)
        sys.exit(1)
    with open(DATA_FILE) as f:
        return BalfourProject.model_validate(json.load(f))


def save_project(project: BalfourProject) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(project.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        f.write("\n")


def cmd_render(_args: argparse.Namespace) -> None:
    project = load_project()
    render_all(project, REPO_ROOT)
    print("Rendered all Markdown files from balfour.json")


def cmd_fetch(_args: argparse.Namespace) -> None:
    project = load_project()
    results = fetch_prices(project)
    save_project(project)
    print(f"Fetched {results['checked']} URLs: {results['success']} ok, {results['broken']} broken, {results['unavailable']} unavailable")


def cmd_validate(_args: argparse.Namespace) -> None:
    project = load_project()
    results = validate_urls(project)
    if results["total"] == 0:
        print("No product URLs configured yet.")
    else:
        print(f"Validated {results['total']} URLs: {results['reachable']} reachable, {results['unreachable']} unreachable")


def cmd_report(args: argparse.Namespace) -> None:
    project = load_project()
    report_type = args.report_type
    if report_type == "needs":
        report_needs(project)
    elif report_type == "totals":
        report_totals(project)
    elif report_type == "status":
        report_status(project)
    else:
        print(f"Unknown report type: {report_type}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="price-tracker", description="Balfour material selection tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("render", help="Generate all Markdown files from JSON")

    sub.add_parser("fetch", help="Fetch/validate prices and update JSON")

    sub.add_parser("validate", help="Check all product URLs are reachable")

    report_parser = sub.add_parser("report", help="Print reports")
    report_parser.add_argument("report_type", choices=["needs", "totals", "status"])

    args = parser.parse_args()
    commands = {"render": cmd_render, "fetch": cmd_fetch, "validate": cmd_validate, "report": cmd_report}
    commands[args.command](args)


if __name__ == "__main__":
    main()
