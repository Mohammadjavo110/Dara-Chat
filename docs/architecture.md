# Architecture

Short map of the research harness: components, graph flow, and one full run.
Sources: `src/research_harness/graph.py`, `state.py`, `tools.py`, `app.py`, `config.py`.
Diagram sources live in `docs/diagrams/` (`.mmd` files).

## Components

| Component | File | Role |
|-----------|------|------|
| Streamlit UI | `app.py` | Hero search, live step status, Answer/Links tabs, sidebar history |
| Graph wiring | `graph.py` | `StateGraph` nodes + `decide_router` stop rule |
| Shared state | `state.py` | `ResearchState`: question, queries, fetched, extracted, rounds, answer |
| Tool nodes | `tools.py` | SerpApi search, Firefox/MarkItDown fetch, LLM extract/synthesize |
| History helpers | `history.py` | Newest-first cap, entry labels, delete |
| Caps | `config.py` | `MAX_ROUNDS=3`, `MIN_USEFUL_SOURCES=3`, char budgets, timeouts |

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

## One run, end to end

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
