import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "app": "betlens-api", "message": "%(message)s"}',
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )


logger = logging.getLogger("betlens")