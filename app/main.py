import logging

from db import wait_for_db
from executor import wait_for_selenium
from scheduler import build_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Menunggu database siap...")
    wait_for_db()

    logger.info("Menunggu Selenium siap...")
    wait_for_selenium()

    scheduler = build_scheduler()
    logger.info("Scheduler dimulai. Menunggu jadwal task berikutnya...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler dihentikan.")
