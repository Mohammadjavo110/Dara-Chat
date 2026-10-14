"""Shared knobs for the harness.

Caps exist so the agent can never loop forever: every `search` pass
increments `rounds`, and `decide` must stop at MAX_ROUNDS even when
information is still thin (then the answer states the limitation).
"""

MAX_ROUNDS = 3
RESULTS_PER_QUERY = 3  # per query; the extractor keeps only the first MAX_SOURCES
MAX_SOURCES = 5
MIN_USEFUL_SOURCES = 3
MAX_CHARS_PER_PAGE = 30_000
MAX_CHARS_TOTAL = 250_000
# Budget math: 5 sources x 30k = 150k <= 250k total, so the extractor model
# always receives all 5 fetched docs in ONE chat within its 500k context.

SEARCH_TIMEOUT_S = 30
FETCH_TIMEOUT_MS = 10_000

SERPAPI_API_KEY_ENV = "SERPAPI_API_KEY"
LLM_BASE_URL_ENV = "LLM_BASE_URL"
LLM_API_KEY_ENV = "LLM_API_KEY"
LLM_MODEL_ENV = "LLM_MODEL"
EXTRACTOR_BASE_URL_ENV = "EXTRACTOR_BASE_URL"
EXTRACTOR_API_KEY_ENV = "EXTRACTOR_API_KEY"
EXTRACTOR_MODEL_ENV = "EXTRACTOR_MODEL"

# Fallback excerpt size when the extractor reply cannot be split per source.
EXTRACT_FALLBACK_CHARS = 2000
