from __future__ import annotations

import logging
import sys

import anyio

from config import get_settings
from core.run_worker import RunWorker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def _main():
    cfg = get_settings()
    logger.info(
        "Starting DataAgent run worker mysql=%s:%s session_db=%s",
        cfg.mysql_host,
        cfg.mysql_port,
        cfg.session_mysql_database,
    )
    worker = RunWorker()
    await worker.run_forever()


if __name__ == "__main__":
    anyio.run(_main)
