# Dara-Chat

# Research Harness — local research agent (LangGraph + Streamlit)

> Status: phase 3 (Streamlit UI with live progress + sidebar history).

Small local Perplexity-like: user topic -> planned queries -> SerpApi search ->
Playwright Firefox + MarkItDown fetch -> secondary-model extraction ->
capped `decide` loop (`MAX_ROUNDS=3`) -> cited answer in Streamlit.

## Setup

```bash
make install
cp .env.example .env   # fill SERPAPI_API_KEY etc.
```

`pyproject.toml` uses the Aliyun PyPI mirror as default index because
`files.pythonhosted.org` DNS is unreachable from this network. To use stock
PyPI, delete the `[[tool.uv.index]]` block or set `UV_DEFAULT_INDEX`.

Needs: Python >= 3.13, `uv`, Firefox browser files (`make install` fetches them).

## Make commands

- `make install` — `uv sync` + Playwright Firefox
- `make test` — offline `pytest` (no network/services)
- `make run` — Streamlit UI (from phase 3)

## Structure

- `src/research_harness/config.py` — caps, timeouts, env key names
- `src/research_harness/state.py` — shared `ResearchState`
- `src/research_harness/graph.py` — LangGraph wiring (phase 1)
- `src/research_harness/tools.py` — search/fetch/extract (phase 2)
- `src/research_harness/app.py` — Streamlit UI (phase 3)
- `src/research_harness/history.py` — sidebar history helpers
- `tests/` — offline harness tests

### System architecture

```mermaid
flowchart TD
    User(["User"]) --> UI["app.py<br/>Streamlit UI"]
    UI --> Graph["graph.py<br/>StateGraph"]
    Graph --> State["state.py<br/>ResearchState"]
    Graph --> Plan["plan_queries"]
    Graph --> Search["search"]
    Graph --> Fetch["fetch"]
    Graph --> Extract["extract"]
    Graph --> Synth["synthesize"]
    Search --> SerpAPI["SerpApi<br/>web search"]
    Fetch --> Pages["Web pages<br/>Firefox + MarkItDown"]
    Extract --> ExtLLM["Extractor LLM<br/>Cline GLM"]
    Synth --> MainLLM["Main LLM<br/>Cline DeepSeek"]

    classDef ui fill:#87CEEB,stroke:#333,stroke-width:2px,color:darkblue
    classDef core fill:#90EE90,stroke:#333,stroke-width:2px,color:darkgreen
    classDef ext fill:#F0F0F0,stroke:#333,stroke-width:2px,color:black
    class User,UI ui
    class Graph,State,Plan,Search,Fetch,Extract,Synth core
    class SerpAPI,Pages,ExtLLM,MainLLM ext
```

## Graph flow

`plan_queries -> search -> fetch -> extract -> decide`
(`decide -> search` while info is thin and `rounds < MAX_ROUNDS`,
else `-> synthesize -> END`; on cap with thin info the answer states the limit.)

```mermaid
flowchart TD
    START(["START"]) --> PlanQ["plan_queries<br/>2-3 search queries"]
    PlanQ --> Search["search<br/>SerpApi top links"]
    Search --> Fetch["fetch<br/>page markdown"]
    Fetch --> Extract["extract<br/>query-relevant excerpts"]
    Extract --> Decide{"decide<br/>rounds &lt; 3<br/>useful &lt; 3?"}
    Decide -->|yes| Search
    Decide -->|no| Synth["synthesize<br/>cited answer"]
    Synth --> DONE(["END"])

    classDef node fill:#90EE90,stroke:#333,stroke-width:2px,color:darkgreen
    classDef gate fill:#FFD700,stroke:#333,stroke-width:2px,color:black
    classDef term fill:#87CEEB,stroke:#333,stroke-width:2px,color:darkblue
    class PlanQ,Search,Fetch,Extract,Synth node
    class Decide gate
    class START,DONE term
```

## Run sequence

One research run, from question to answer (live step updates included):

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit app
    participant G as LangGraph
    participant S as SerpApi
    participant W as Web pages
    participant L as Cline LLMs

    U->>UI: research question
    activate UI
    UI->>G: invoke ResearchState
    activate G
    G->>L: plan_queries
    L-->>G: 2-3 queries
    loop until enough sources or round cap
        G->>S: search per query
        S-->>G: links
        G->>W: fetch pages
        W-->>G: markdown
        G->>L: extract excerpts
        L-->>G: extracted sources
    end
    G->>L: synthesize answer
    L-->>G: cited answer
    G-->>UI: result + steps
    deactivate G
    UI-->>U: answer, links, history
    deactivate UI
```

## Known limits

- Fetch keeps bounded markdown per page; big pages are truncated.
- Web content is treated as data only; in-page instructions are ignored.
