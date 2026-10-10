"""Shared graph state: the single box every node reads and writes."""

from typing import TypedDict


class Source(TypedDict):
    url: str
    title: str
    snippet: str
    text: str  # full bounded markdown, filled by fetch


class ExtractedSource(TypedDict):
    url: str
    excerpt: str  # query-relevant part, picked by the extractor model


class ResearchState(TypedDict):
    question: str
    queries: list[str]
    fetched: list[Source]
    extracted: list[ExtractedSource]
    rounds: int
    answer: str
