"""
Controla quais URLs já foram processadas por fonte.
Estado persistido em state/seen/<source_id>.json (versionado no repo).
"""
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

STATE_DIR = Path(__file__).parent.parent / "state" / "seen"
STATE_DIR.mkdir(parents=True, exist_ok=True)

MAX_SEEN = 500  # máximo de URLs armazenadas por fonte


def _state_path(source_id: str) -> Path:
    return STATE_DIR / f"{source_id}.json"


def _load(source_id: str) -> set:
    path = _state_path(source_id)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def _save(source_id: str, seen: set):
    path = _state_path(source_id)
    # Mantém apenas as MAX_SEEN mais recentes (lista para preservar inserção)
    seen_list = list(seen)[-MAX_SEEN:]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seen_list, f, ensure_ascii=False, indent=2)


def is_new(source_id: str, url: str) -> bool:
    if not url:
        return False
    return url not in _load(source_id)


def mark_seen(source_id: str, url: str):
    seen = _load(source_id)
    seen.add(url)
    _save(source_id, seen)
