"""Phase-1: stop-after-cap behavior, fully offline (stubbed nodes, no network/LLM)."""

from research_harness import config
from research_harness.graph import build_graph, decide_router


def _empty_state():
    return {
        "question": "best search API?",
        "queries": [],
        "fetched": [],
        "extracted": [],
        "rounds": 0,
        "answer": "",
    }


def test_router_stops_at_cap_even_with_no_info():
    state = _empty_state()
    state["rounds"] = config.MAX_ROUNDS  # cap reached, zero sources
    assert decide_router(state) == "synthesize"


def test_router_searches_again_when_thin_and_below_cap():
    state = _empty_state()  # rounds=0, no sources
    assert decide_router(state) == "search"


def test_router_synthesizes_when_enough_sources():
    state = _empty_state()
    state["fetched"] = [
        {"url": f"https://example.com/{i}", "title": "t", "snippet": "s", "text": "body"}
        for i in range(config.MIN_USEFUL_SOURCES)
    ]
    assert decide_router(state) == "synthesize"


def test_full_run_stops_after_cap_and_marks_limitation():
    calls = {"search": 0}

    def stub_plan(state):
        return {"queries": ["q1"]}

    def stub_search(state):
        calls["search"] += 1
        item = {
            "url": f"https://example.com/{calls['search']}",
            "title": "t",
            "snippet": "s",
            "text": "",
        }
        return {"fetched": state["fetched"] + [item], "rounds": state["rounds"] + 1}

    def stub_fetch(state):
        return {"fetched": [{**it, "text": "body"} for it in state["fetched"]]}

    def stub_extract(state):
        return {"extracted": [{"url": it["url"], "excerpt": "rel"} for it in state["fetched"]]}

    def stub_synth(state):
        limited = state["rounds"] >= config.MAX_ROUNDS
        return {"answer": ("LIMITED: " if limited else "") + "done"}

    app = build_graph(
        plan_queries=stub_plan,
        search=stub_search,
        fetch=stub_fetch,
        extract=stub_extract,
        synthesize=stub_synth,
    )
    result = app.invoke(_empty_state())

    # Loop ran exactly to the cap — never more, never infinite.
    assert calls["search"] == config.MAX_ROUNDS
    assert result["rounds"] == config.MAX_ROUNDS
    # Cap hit with thin info: the answer must say so.
    assert "LIMITED" in result["answer"]
