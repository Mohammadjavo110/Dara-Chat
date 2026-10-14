"""Phase-2: real-tool behavior, fully offline (fakes, no network/LLM/keys)."""

import pytest

from research_harness import config, tools
from research_harness.tools import MissingConfig


class FakeLLM:
    def __init__(self, text):
        self.text = text
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt
        return self.text


def _fetched(n, with_text=True):
    return [
        {
            "url": f"https://example.com/{i}",
            "title": "t",
            "snippet": "s",
            "text": "body" if with_text else "",
        }
        for i in range(n)
    ]


def _state(**over):
    base = {
        "question": "best search API?",
        "queries": ["q1"],
        "fetched": [],
        "extracted": [],
        "rounds": 0,
        "answer": "",
    }
    base.update(over)
    return base


def test_search_missing_key_names_env_var(monkeypatch):
    monkeypatch.delenv(config.SERPAPI_API_KEY_ENV, raising=False)
    with pytest.raises(MissingConfig, match=config.SERPAPI_API_KEY_ENV):
        tools.search(_state())


def test_make_llm_missing_config_names_vars(monkeypatch):
    monkeypatch.delenv(config.LLM_API_KEY_ENV, raising=False)
    with pytest.raises(MissingConfig, match=config.LLM_API_KEY_ENV):
        tools.make_llm(config.LLM_MODEL_ENV + "_X", config.LLM_API_KEY_ENV, "m")


def test_plan_parses_json_list():
    out = tools.plan_queries(_state(), llm=FakeLLM('["a", "b"]'))
    assert out == {"queries": ["a", "b"]}


def test_plan_falls_back_to_question_on_broken_json():
    out = tools.plan_queries(_state(question="my topic"), llm=FakeLLM("not json"))
    assert out == {"queries": ["my topic"]}


def test_extract_keeps_first_max_sources_with_urls():
    llm = FakeLLM("ok")
    out = tools.extract(_state(fetched=_fetched(7)), llm=llm)
    assert len(out["extracted"]) == config.MAX_SOURCES
    assert out["extracted"][0]["url"] == "https://example.com/0"
    assert "[SOURCE 1 URL: https://example.com/0]" in llm.last_prompt
    assert "UNTRUSTED" in llm.last_prompt


def test_fetch_skips_failed_page(monkeypatch):
    def fake_page(url):
        if "bad" in url:
            raise RuntimeError("boom")
        return "text"

    monkeypatch.setattr(tools, "fetch_page", fake_page)
    state = _state(
        fetched=[
            {"url": "https://good.com", "title": "t", "snippet": "s", "text": ""},
            {"url": "https://bad.com", "title": "t", "snippet": "s", "text": ""},
        ]
    )
    out = tools.fetch(state)
    assert [f["url"] for f in out["fetched"]] == ["https://good.com"]
    assert out["fetched"][0]["text"] == "text"


def test_synthesize_marks_limitation_at_cap_and_cites_urls():
    llm = FakeLLM("done")
    state = _state(rounds=config.MAX_ROUNDS, extracted=[{"url": "https://a.com", "excerpt": "e"}])
    out = tools.synthesize(state, llm=llm)
    assert out == {"answer": "done"}
    assert "Limited research: True" in llm.last_prompt
    assert "https://a.com" in llm.last_prompt


def test_extract_content_reads_standard_envelope():
    payload = {"choices": [{"message": {"content": "hi"}}]}
    assert tools._extract_content(payload) == "hi"


def test_extract_content_reads_cline_wrapped_envelope():
    payload = {"choices": None, "data": {"choices": [{"message": {"content": "hey"}}]}}
    assert tools._extract_content(payload) == "hey"


def test_extract_content_rejects_empty_choices():
    with pytest.raises(ValueError):
        tools._extract_content({"choices": None, "data": {}})


def test_html_to_markdown_keeps_headings_and_links():
    html = '<h1>Title</h1><p>See <a href="https://x.com">X</a></p>'
    md = tools._html_to_markdown(html, "https://x.com")
    assert "Title" in md
    assert "https://x.com" in md
