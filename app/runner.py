import json
import logging
import os

from db import log_start, log_success, log_failure
from executor import build_driver, run_steps

logger = logging.getLogger(__name__)
SCREENSHOT_DIR = "/app/screenshots"


def run_task(task_name, target_url, steps_json):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    log_id = log_start(task_name)
    driver = None
    try:
        steps = steps_json if isinstance(steps_json, list) else json.loads(steps_json)
        driver = build_driver()
        message = run_steps(driver, target_url, steps, SCREENSHOT_DIR, task_name)
        log_success(log_id, message)
        logger.info("Task selesai: %s", task_name)
    except Exception as e:
        logger.exception("Task gagal: %s", task_name)
        error_msg = str(e)
        if driver is not None:
            try:
                path = os.path.join(SCREENSHOT_DIR, f"{task_name}_error.png")
                driver.save_screenshot(path)
                error_msg += f" (lihat screenshot: {path})"
            except Exception:
                pass
        log_failure(log_id, error_msg)
    finally:
        if driver is not None:
            driver.quit()
