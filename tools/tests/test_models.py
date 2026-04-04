import json
from pathlib import Path

from price_tracker.models import BalfourProject, MaterialSelection, SelectionStatus


def test_load_balfour_json():
    data_file = Path(__file__).resolve().parents[2] / "balfour" / "data" / "balfour.json"
    if not data_file.exists():
        return  # skip if JSON not built yet

    with open(data_file) as f:
        data = json.load(f)

    project = BalfourProject.model_validate(data)
    assert project.project.name == "Balfour"
    assert len(project.contractors) > 0
    assert len(project.suppliers) > 0
    assert len(project.decisions) > 0


def test_selection_recalculate():
    sel = MaterialSelection(
        id="test",
        item_name="Test Item",
        description="Test",
        unit_price=10.0,
        quantity=100,
        waste_factor=0.10,
        tax_rate=0.06,
    )
    sel.recalculate()
    assert sel.subtotal == 1100.0  # 100 * 1.10 * $10
    assert sel.tax_amount == 66.0  # 1100 * 0.06
    assert sel.total_with_tax == 1166.0


def test_selection_no_price():
    sel = MaterialSelection(id="test", item_name="Test", description="Test")
    sel.recalculate()
    assert sel.subtotal is None
    assert sel.total_with_tax is None


def test_selection_status_default():
    sel = MaterialSelection(id="test", item_name="Test", description="Test")
    assert sel.status == SelectionStatus.NEEDS_SELECTION
