"""Perplexity-style UI: dark hero search, Answer/Links tabs, follow-up box (RTL answers)."""

import logging
import re
import time

import streamlit as st

from research_harness import history, tools
from research_harness.graph import build_graph

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

st.set_page_config(page_title="Research", layout="wide", initial_sidebar_state="expanded")

DARK_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
@import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
header[data-testid="stHeader"] { background: transparent; }
div[data-testid="stToolbar"], footer { visibility: hidden; }
button[data-testid="stExpandSidebarButton"] { visibility: visible !important; }
.stApp { font-family: 'Inter', 'Vazirmatn', Tahoma, sans-serif; }
[data-testid="stMainBlockContainer"] { max-width: 780px; }
.hero { text-align: center; margin: 14vh auto 1.4rem auto; }
.hero .kicker { color: #8a8a8a; font-size: 0.8rem; margin-bottom: 0.4rem; }
.hero h1 { font-weight: 500; font-size: 1.8rem; margin: 0; }
div[data-testid="stForm"] { border: 1px solid #2b2b2c; border-radius: 16px; padding: 0.9rem; background: #141415; }
div[data-testid="stForm"] .stButton > button {
  border-radius: 999px; min-height: 44px; width: 100%;
  background: #e8e8e6; color: #111; font-weight: 600; border: none; cursor: pointer;
}
div[data-testid="stForm"] .stButton > button:hover { background: #fff; }
div[data-testid="stForm"] .stButton > button:focus-visible { outline: 2px solid #4fb3bd; outline-offset: 2px; }
.query-bubble { background: #1f1f20; border-radius: 12px; padding: 0.6rem 1rem;
  width: fit-content; margin-left: auto; font-family: 'Vazirmatn', 'Inter', sans-serif;
  direction: rtl; text-align: right; }
.meta { color: #8a8a8a; font-size: 0.8rem; margin: 0.3rem 0; }
.answer { direction: rtl; text-align: right; font-family: 'Vazirmatn', 'Inter', sans-serif;
  line-height: 2.1; font-size: 1rem; }
.answer .ltr, .answer code, .answer .katex { direction: ltr !important; unicode-bidi: isolate !important; display: inline-block; }
.answer table { direction: rtl; width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
.answer th, .answer td { border: 1px solid #2b2b2c; padding: 0.6rem 0.8rem; text-align: right; }
.answer th { background: #1a1a1b; }
.src-card { background: #141415; border: 1px solid #262627; border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 0.6rem; }
.src-num { display: inline-flex; width: 1.4rem; height: 1.4rem; border-radius: 6px;
  background: #20808d; color: #fff; font-size: 0.75rem; align-items: center; justify-content: center; margin-right: 0.5rem; }
@media (max-width: 768px) { .hero { margin-top: 7vh; } .hero h1 { font-size: 1.35rem; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
"""
st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)


def render_answer(text: str) -> str:
    """Fix legacy bracket-math, isolate LaTeX LTR so RTL doesn't flip it."""
    text = re.sub(
        r"\[\s*([^\[\]\n]*?(?:\\[a-zA-Z]+|\^|=)[^\[\]\n]*?)\s*\](?!\()",
        r"$$\1$$",
        text,
    )
    text = re.sub(
        r"(\$\$.+?\$\$|\$.+?\$)",
        r'<span class="ltr" dir="ltr">\1</span>',
        text,
        flags=re.DOTALL,
    )
    return text


def run_research(question: str) -> dict:
    main_llm = tools.default_llm()
    extractor_llm = tools.default_extractor_llm()
    steps: list[str] = []
    t0 = time.time()
    with st.status("Researching...", expanded=True) as status:
        status.write("Planning queries...")

        def on_query(q: str) -> None:
            msg = f"Searching: {q}"
            steps.append(msg)
            status.write(msg)

        def on_fetch(n: int) -> None:
            msg = f"Read {n} pages"
            steps.append(msg)
            status.write(msg)

        app = build_graph(
            plan_queries=lambda s: tools.plan_queries(s, llm=main_llm),
            search=lambda s: tools.search(s, on_progress=on_query),
            fetch=lambda s: tools.fetch(s, on_progress=on_fetch),
            extract=lambda s: tools.extract(s, llm=extractor_llm),
            synthesize=lambda s: tools.synthesize(s, llm=main_llm),
        )
        result = app.invoke(
            {"question": question, "queries": [], "fetched": [], "extracted": [], "rounds": 0, "answer": ""}
        )
        status.update(label=f"Done — {len(steps)} steps", state="complete")
    result["duration_s"] = time.time() - t0
    result["question"] = question
    result["steps"] = steps
    return result


if "threads" not in st.session_state:
    st.session_state.threads = []
if "current" not in st.session_state:
    st.session_state.current = None

with st.sidebar:
    st.markdown("**Research**")
    if st.button("New thread", use_container_width=True):
        st.session_state.current = None
        st.rerun()
    st.caption("History")
    threads = st.session_state.threads
    for idx, th in history.visible_history(threads):
        label, meta = history.format_entry(th)
        is_cur = th is st.session_state.current
        row = st.columns([5, 1])
        with row[0]:
            if st.button(
                ("› " if is_cur else "") + (label or "(untitled)"),
                key=f"hist-{idx}",
                use_container_width=True,
                disabled=is_cur,
            ):
                st.session_state.current = th
                st.rerun()
        with row[1]:
            if st.button("✕", key=f"del-{idx}"):
                st.session_state.threads = history.remove_at(threads, idx)
                if is_cur:
                    st.session_state.current = None
                st.rerun()
        if meta:
            st.caption(meta)
    if threads and st.button("Clear all", key="hist-clear", use_container_width=True):
        st.session_state.threads = []
        st.session_state.current = None
        st.rerun()

cur = st.session_state.current

if cur is None:
    st.markdown('<div class="hero"><div class="kicker">Search</div><h1>What do you want to know?</h1></div>', unsafe_allow_html=True)
    with st.form("search"):
        q = st.text_input("Ask", placeholder="Type your question... (فارسی یا English)", label_visibility="collapsed")
        submitted = st.form_submit_button("Research")
    if submitted and q and q.strip():
        try:
            res = run_research(q.strip())
            res["created_at"] = time.time()
            st.session_state.threads.append(res)
            st.session_state.current = res
            st.rerun()
        except tools.MissingConfig as exc:
            st.error(f"Missing config — {exc}")
        except Exception as exc:  # noqa: BLE001
            log.exception("research run failed")
            st.error(f"Research failed: {exc}")
else:
    st.markdown(f'<div class="query-bubble">{cur["question"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="meta">Researched {cur.get("duration_s", 0):.0f}s</div>', unsafe_allow_html=True)
    tab_answer, tab_links = st.tabs(["Answer", "Links"])
    with tab_answer:
        st.markdown(f'<div class="answer">{render_answer(cur.get("answer", ""))}</div>', unsafe_allow_html=True)
    with tab_links:
        items = cur.get("extracted") or cur.get("fetched") or []
        if not items:
            st.info("No sources.")
        for n, item in enumerate(items, 1):
            url = item.get("url", "")
            title = item.get("title") or url
            st.markdown(
                f'<div class="src-card" dir="auto"><span class="src-num">{n}</span>'
                f'<a href="{url}" target="_blank">{title}</a><br><span style="color:#8a8a8a;font-size:0.8rem">{url}</span></div>',
                unsafe_allow_html=True,
            )
    follow = st.chat_input("Ask a follow-up...")
    if follow and follow.strip():
        try:
            res = run_research(follow.strip())
            res["created_at"] = time.time()
            st.session_state.threads.append(res)
            st.session_state.current = res
            st.rerun()
        except tools.MissingConfig as exc:
            st.error(f"Missing config — {exc}")
        except Exception as exc:  # noqa: BLE001
            log.exception("research run failed")
            st.error(f"Research failed: {exc}")
