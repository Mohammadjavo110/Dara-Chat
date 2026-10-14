"""Graph wiring: node order, shared state, and the stop rule.

Nodes are injected as callables so tests can stub them (offline) while
phase 2 plugs in the real SerpApi/Playwright/LLM implementations.
`decide` is a pass-through node: it writes nothing, the `decide_router`
conditional edge alone chooses search-again vs synthesize.
"""

from langgraph.graph import END, START, StateGraph

from research_harness import config
from research_harness.state import ResearchState


def decide_router(state: ResearchState) -> str:
    """Search again only while below cap AND info is still thin."""
    useful = sum(1 for f in state["fetched"] if f.get("text"))
    if state["rounds"] < config.MAX_ROUNDS and useful < config.MIN_USEFUL_SOURCES:
        return "search"
    # Cap reached or enough info: synthesize (caller marks limitation on cap).
    return "synthesize"


def build_graph(*, plan_queries, search, fetch, extract, synthesize):
    graph = StateGraph(ResearchState)
    graph.add_node("plan_queries", plan_queries)
    graph.add_node("search", search)
    graph.add_node("fetch", fetch)
    graph.add_node("extract", extract)
    graph.add_node("decide", lambda state: {})
    graph.add_node("synthesize", synthesize)

    graph.add_edge(START, "plan_queries")
    graph.add_edge("plan_queries", "search")
    graph.add_edge("search", "fetch")
    graph.add_edge("fetch", "extract")
    graph.add_edge("extract", "decide")
    graph.add_conditional_edges(
        "decide", decide_router, {"search": "search", "synthesize": "synthesize"}
    )
    graph.add_edge("synthesize", END)
    return graph.compile()
