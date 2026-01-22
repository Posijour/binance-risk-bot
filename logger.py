import json
import os
import time
from threading import Lock

_LOG_TO_FILE = os.getenv("LOG_TO_FILE", "").lower() in ("1", "true", "yes")
_LOG_FILE = "events.jsonl"

_lock = Lock()


def log_event(event: str, payload: dict):
    """
    Универсальный логгер событий бота.
    - В проде (Render): пишет в stdout (через print)
    - Локально (LOG_TO_FILE=true): пишет в events.jsonl
    """
    record = {
        "ts": int(time.time()),
        "event": event,
        **payload,
    }

    line = json.dumps(record, ensure_ascii=False)

    with _lock:
        if _LOG_TO_FILE:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        else:
            print(line, flush=True)
