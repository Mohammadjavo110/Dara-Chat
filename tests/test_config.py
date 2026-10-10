"""Phase-0 smoke tests: config caps and state shape (fully offline)."""

from research_harness import config
from research_harness.state import ResearchState


def test_stop_cap_is_small_and_positive():
    assert 1 <= config.MAX_ROUNDS <= 5


def test_source_budget_fits_extractor_context():
    assert config.MAX_SOURCES * config.MAX_CHARS_PER_PAGE <= config.MAX_CHARS_TOTAL


def test_state_holds_all_harness_fields():
    state: ResearchState = {
        "question": "q",
        "queries": ["a", "b"],
        "fetched": [],
        "extracted": [],
        "rounds": 0,
        "answer": "",
    }
    assert state["rounds"] == 0
    assert state["queries"] == ["a", "b"]
