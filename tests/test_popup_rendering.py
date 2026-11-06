from pathlib import Path


POPUP_SCRIPT = Path(__file__).parents[1] / "extension" / "popup.js"


def test_popup_renders_untrusted_values_as_text_not_html():
    source = POPUP_SCRIPT.read_text(encoding="utf-8")

    assert "innerHTML" not in source
    assert "insertAdjacentHTML" not in source
    assert "valueEl.textContent = value;" in source
    assert "finding.explanation" in source
    assert "finding.evidence" in source
    assert "safetyReport.explanation" in source
    assert "textContent =" in source
