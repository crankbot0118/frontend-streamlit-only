"""Central logging setup for all VIGT services."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from config.settings import logging_config

_root_configured = False


def setup_logging(service: str) -> logging.Logger:
    """Configure the shared ``vigt`` logger tree once, then return a service logger."""
    global _root_configured

    cfg = logging_config()
    root = logging.getLogger("vigt")
    service_logger = logging.getLogger(f"vigt.{service}")

    if not _root_configured:
        root.setLevel(cfg.level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

        if cfg.to_file:
            cfg.directory.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                cfg.directory / "vigt.log",
                maxBytes=cfg.max_bytes,
                backupCount=cfg.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)

        _root_configured = True

    return service_logger
