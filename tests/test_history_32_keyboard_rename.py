"""History: allow keyboard users to activate model rename."""

from pathlib import Path


PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_model_rename_cell_is_keyboard_focusable_and_supports_enter_space():
    assert "modelTd.tabIndex = 0;" in PAGE
    assert "modelTd.setAttribute('role', 'button');" in PAGE
    assert "modelTd.onclick = () => editModelName(modelTd, m);" in PAGE
    assert "if (e.key === 'Enter' || e.key === ' ')" in PAGE
    assert "editModelName(modelTd, m);" in PAGE
