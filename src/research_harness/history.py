"""Rich sidebar history helpers (pure, Streamlit-free)."""

from datetime import datetime

MAX_HISTORY = 10


def visible_history(threads, limit=MAX_HISTORY):
    """(original_index, thread) pairs, newest first, capped at limit."""
    indexed = list(enumerate(threads))
    return indexed[-limit:][::-1] if limit else []


def format_entry(thread):
    """(label, meta): full question plus time, duration and step count."""
    label = thread.get("question", "")
    parts = []
    created = thread.get("created_at")
    if created:
        try:
            parts.append(datetime.fromtimestamp(created).strftime("%H:%M"))
        except (OSError, OverflowError, ValueError):
            pass
    if thread.get("duration_s") is not None:
        parts.append(f"{thread['duration_s']:.0f}s")
    if thread.get("steps") is not None:
        parts.append(f"{len(thread['steps'])} steps")
    return label, " · ".join(parts)


def remove_at(threads, idx):
    """New list without threads[idx]; input untouched."""
    return [t for i, t in enumerate(threads) if i != idx]
