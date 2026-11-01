"""History: persist temperature plans across browser refreshes."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_plans_are_saved_to_and_loaded_from_local_storage():
    assert "const PLAN_STORAGE_KEY = 'homebench.plans';" in HTML
    assert "localStorage.setItem(PLAN_STORAGE_KEY" in HTML
    assert "localStorage.getItem(PLAN_STORAGE_KEY)" in HTML
    assert "function savePlans()" in HTML
    assert "function loadSavedPlans()" in HTML
    assert "runsInput.oninput = savePlans;" in HTML
    assert "tempInput.oninput = savePlans;" in HTML


def test_saved_plans_are_restored_before_the_default_row():
    init = HTML.split("(async () => {", 1)[1]

    assert "const savedPlans = loadSavedPlans();" in init
    assert init.index("const savedPlans = loadSavedPlans();") < init.index(
        "addPlanRow(1, 0.0);"
    )
    assert "addPlanRow(1, 0.0);" in HTML
