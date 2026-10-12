"""Streamlit UI: topic in, cited answer + source links out."""

import logging

import streamlit as st

from research_harness import tools
from research_harness.graph import build_graph

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

st.title("هارنس تحقیق محلی")
topic = st.text_input("موضوع یا سؤال تحقیق")

if st.button("شروع تحقیق"):
    if not topic.strip():
        st.warning("اول یک موضوع بنویس.")
    else:
        try:
            main_llm = tools.default_llm()
            extractor_llm = tools.default_extractor_llm()
            app = build_graph(
                plan_queries=lambda s: tools.plan_queries(s, llm=main_llm),
                search=tools.search,
                fetch=tools.fetch,
                extract=lambda s: tools.extract(s, llm=extractor_llm),
                synthesize=lambda s: tools.synthesize(s, llm=main_llm),
            )
            with st.status("در حال تحقیق...") as status:
                status.write("جست‌وجو و خواندن منابع...")
                result = app.invoke(
                    {
                        "question": topic.strip(),
                        "queries": [],
                        "fetched": [],
                        "extracted": [],
                        "rounds": 0,
                        "answer": "",
                    }
                )
                status.update(label="تحقیق تمام شد", state="complete")
            st.markdown(result["answer"])
            st.subheader("منابع")
            for item in result["extracted"] or result["fetched"]:
                st.markdown(f"- [{item.get('title') or item['url']}]({item['url']})")
        except tools.MissingConfig as exc:
            log.warning("missing config: %s", exc)
            st.error(f"تنظیم ناقص است — {exc}")
        except Exception as exc:  # noqa: BLE001 - last resort, user-friendly
            log.exception("research run failed")
            st.error(f"تحقیق ناموفق بود: {exc}")
