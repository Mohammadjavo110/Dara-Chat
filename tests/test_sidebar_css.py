"""Sidebar must stay reopenable: hiding the toolbar must not hide its expand button."""

import re
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "src" / "research_harness" / "app.py"


def test_expand_sidebar_button_stays_visible():
    src = APP.read_text(encoding="utf-8")
    assert "stExpandSidebarButton" in src
    assert re.search(r"stExpandSidebarButton.{0,120}visibility:\s*visible", src)
