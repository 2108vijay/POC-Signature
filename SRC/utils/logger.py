import sys
import logging
import json
from pathlib import Path
from loguru import logger

Path("logs").mkdir(exist_ok=True)

logger.remove()


logger.add(
    lambda msg: sys.stdout.write(json.dumps(json.loads(msg), indent=2) + "\n"),
    serialize=True,
    level="INFO",
)


logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler()]
    logging_logger.propagate = False

__all__ = ["logger"]