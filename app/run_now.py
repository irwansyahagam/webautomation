"""
Jalankan task tertentu secara manual, tanpa menunggu jadwal cron.
Berguna untuk testing selector/step sebelum diaktifkan otomatis.

Cara pakai (dari luar container):
    docker compose exec app python run_now.py contoh_isi_form_login
"""
import sys
import logging

from db import get_active_tasks, wait_for_db
from executor import wait_for_selenium
from runner import run_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Pemakaian: python run_now.py <task_name>")
        sys.exit(1)

    target_task_name = sys.argv[1]

    wait_for_db()
    wait_for_selenium()

    tasks = {row["task_name"]: row for row in get_active_tasks()}
    task = tasks.get(target_task_name)

    if not task:
        logger.error("Task '%s' tidak ditemukan di tabel automation_tasks", target_task_name)
        sys.exit(1)

    logger.info("Menjalankan task '%s' secara manual...", target_task_name)
    run_task(task["task_name"], task["target_url"], task["steps_json"])
    logger.info("Selesai. Cek tabel automation_logs untuk detail hasilnya.")
