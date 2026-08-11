import os
import time
import logging
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "webauto")
DB_PASSWORD = os.getenv("DB_PASSWORD", "webauto")
DB_NAME = os.getenv("DB_NAME", "webauto_db")


def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=True,
    )


def wait_for_db(max_retries=30, delay=2):
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_connection()
            conn.close()
            logger.info("Koneksi database berhasil")
            return
        except Exception as e:
            logger.warning("Menunggu database... (%s/%s) - %s", attempt, max_retries, e)
            time.sleep(delay)
    raise RuntimeError("Tidak bisa terhubung ke database setelah beberapa kali percobaan")


def get_active_tasks():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT task_name, target_url, cron_expression, enabled, steps_json FROM automation_tasks"
            )
            return cur.fetchall()
    finally:
        conn.close()


def log_start(task_name):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO automation_logs (task_name, status, started_at) VALUES (%s, 'RUNNING', NOW())",
                (task_name,),
            )
            return cur.lastrowid
    finally:
        conn.close()


def log_success(log_id, message=""):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE automation_logs SET status='SUCCESS', finished_at=NOW(), message=%s WHERE id=%s",
                (message, log_id),
            )
    finally:
        conn.close()


def log_failure(log_id, message=""):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE automation_logs SET status='FAILED', finished_at=NOW(), message=%s WHERE id=%s",
                (message, log_id),
            )
    finally:
        conn.close()
