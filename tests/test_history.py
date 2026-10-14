"""Rich sidebar history: newest-first cap, full-question meta, delete (offline)."""

from research_harness import history


def _thread(i, **over):
    base = {
        "question": f"question number {i} with a long tail to exceed forty chars",
        "duration_s": 12.0,
        "steps": ["a", "b", "c"],
        "created_at": 1_700_000_000.0 + i,
        "answer": "done",
    }
    base.update(over)
    return base


def test_visible_returns_newest_first_capped_at_ten():
    threads = [_thread(i) for i in range(12)]
    visible = history.visible_history(threads)
    assert [idx for idx, _ in visible] == [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]


def test_format_meta_shows_full_question_time_duration_steps():
    label, meta = history.format_entry(_thread(3))
    assert label == "question number 3 with a long tail to exceed forty chars"
    assert "12s" in meta
    assert "3 steps" in meta


def test_format_meta_tolerates_missing_keys():
    label, meta = history.format_entry({"question": "q?"})
    assert label == "q?"
    assert isinstance(meta, str)


def test_remove_at_drops_original_index_and_keeps_rest():
    threads = [_thread(i) for i in range(3)]
    out = history.remove_at(threads, 1)
    assert [t["question"] for t in out] == [
        threads[0]["question"],
        threads[2]["question"],
    ]
    assert len(threads) == 3
