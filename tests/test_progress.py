"""Progress callbacks (summary mode): queries + read counts, offline."""

from research_harness import tools


def _state(**over):
    base = {
        "question": "q?",
        "queries": ["q1", "q2"],
        "fetched": [],
        "extracted": [],
        "rounds": 0,
        "answer": "",
    }
    base.update(over)
    return base


class FakeClient:
    def search(self, engine, q):
        return {"organic_results": [{"link": f"https://x.com/{q}", "title": "t", "snippet": "s"}]}


def test_search_reports_each_query_via_callback():
    seen = []
    out = tools.search(_state(), client=FakeClient(), on_progress=seen.append)
    assert [f["url"] for f in out["fetched"]] == ["https://x.com/q1", "https://x.com/q2"]
    assert seen == ["q1", "q2"]


def test_fetch_reports_read_count_via_callback():
    state = _state(
        fetched=[
            {"url": "https://good.com", "title": "t", "snippet": "s", "text": ""},
            {"url": "https://bad.com", "title": "t", "snippet": "s", "text": ""},
        ]
    )

    def fake_page(url):
        if "bad" in url:
            return None
        return "text"

    seen = []
    out = tools.fetch(state, page_fn=fake_page, on_progress=seen.append)
    assert [f["url"] for f in out["fetched"]] == ["https://good.com"]
    assert seen == [1]
