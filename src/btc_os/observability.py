import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from btc_os.domain import now

RUN_ID = uuid4().hex


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Never serialize arbitrary exceptions/arguments or URLs containing passwords.
        return json.dumps(
            {
                "timestamp": now().isoformat(),
                "run_id": RUN_ID,
                "decision_id": getattr(record, "decision_id", None),
                "correlation_id": getattr(record, "correlation_id", RUN_ID),
                "environment": "INTERNAL_PAPER",
                "source": record.name,
                "severity": record.levelname,
                "event": record.msg if not record.args else "structured_event",
            }
        )


def configure_logs(root: Path) -> logging.Logger:
    directory = root / "logs"
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("btc_os")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            directory / "app.jsonl", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    return logger
