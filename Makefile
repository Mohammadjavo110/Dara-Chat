.PHONY: install run test browser

# Install deps + Playwright Firefox (needed by fetch step)
install:
	uv sync
	uv run playwright install firefox

# Run the Streamlit UI (available from phase 3)
run:
	uv run streamlit run src/research_harness/app.py

# Offline tests (no external network/services required)
test:
	uv run pytest

# Install browsers only
browser:
	uv run playwright install firefox
