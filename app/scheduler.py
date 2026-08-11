import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from db import get_active_tasks
from runner import run_task

logger = logging.getLogger(__name__)


def build_scheduler():
    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    rows = get_active_tasks()

    for row in rows:
        task_name = row["task_name"]
        target_url = row["target_url"]
        cron_expr = row["cron_expression"]
        enabled = row["enabled"]
        steps_json = row["steps_json"]

        if not enabled:
            logger.info("Task %s dinonaktifkan, dilewati", task_name)
            continue

        trigger = CronTrigger.from_crontab(cron_expr, timezone="Asia/Jakarta")
        scheduler.add_job(
            run_task,
            trigger=trigger,
            args=[task_name, target_url, steps_json],
            id=task_name,
            name=task_name,
            replace_existing=True,
        )
        logger.info("Task terdaftar: %s -> %s (%s)", task_name, target_url, cron_expr)

    return scheduler
