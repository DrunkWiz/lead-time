"""Snapshot loading. The app only ever reads these committed files."""
import json
from functools import lru_cache
from pathlib import Path

from .concepts import load_concepts

DATA = Path(__file__).resolve().parent.parent / "data"


def _read(name, default):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def snapshot():
    return _read("series.json", {"weeks": [], "series": {}})


@lru_cache(maxsize=1)
def meta():
    return _read("meta.json", {"fetched_at": None})


@lru_cache(maxsize=1)
def concepts():
    return load_concepts()


@lru_cache(maxsize=1)
def youtube():
    return _read("youtube.json", {"fetched_at": None, "concepts": {}})


def snapshot_date():
    """Default as_of: the end of the last full week in the snapshot."""
    from .series import week_end
    weeks = snapshot()["weeks"]
    return week_end(weeks[-1]).isoformat() if weeks else None
