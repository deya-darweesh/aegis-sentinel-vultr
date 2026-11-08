"""Structured JSON Logger for AegisSentinel.

Formats all application, audit, and security logs into structured JSON
compatible with cloud-native log aggregation.
"""

import json
import logging
import sys
import time


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs one valid JSON record per line."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "task_id": getattr(record, "task_id", None),
            "trace_id": getattr(record, "trace_id", None),
            "containment_status": getattr(record, "containment_status", "NORMAL"),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def configure_logger() -> logging.Logger:
    """Configures the root AegisSentinel structured logger."""
    logger = logging.getLogger("aegis_sentinel")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if re-called
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)

    return logger
