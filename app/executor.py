import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

SELENIUM_URL = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")

SELECTOR_MAP = {
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "id": By.ID,
    "name": By.NAME,
    "class": By.CLASS_NAME,
}


def wait_for_selenium(max_retries=30, delay=2):
    """Tunggu sampai Selenium container siap menerima koneksi."""
    status_url = SELENIUM_URL.replace("/wd/hub", "/status")
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(status_url, timeout=3)
            if r.status_code == 200:
                logger.info("Selenium siap")
                return
        except Exception as e:
            logger.warning("Menunggu Selenium... (%s/%s) - %s", attempt, max_retries, e)
        time.sleep(delay)
    raise RuntimeError("Selenium tidak siap setelah beberapa kali percobaan")


def build_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Remote(command_executor=SELENIUM_URL, options=options)
    return driver


def find(driver, step, timeout=15):
    by = SELECTOR_MAP.get(step.get("selector_type", "css"), By.CSS_SELECTOR)
    selector = step["selector"]
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def run_steps(driver, target_url, steps, screenshot_dir, task_name):
    """
    Jalankan daftar langkah (steps) satu per satu di browser.

    Aksi yang didukung:
    - fill              : isi input teks. Wajib: selector, value
    - click             : klik elemen (button, link, dsb). Wajib: selector
    - select            : pilih opsi dropdown. Wajib: selector, dan value ATAU text
    - wait              : jeda beberapa detik. Wajib: seconds
    - wait_for_element  : tunggu elemen muncul dulu sebelum lanjut. Wajib: selector
    - goto              : pindah ke URL lain di tengah alur. Wajib: url
    - screenshot        : simpan screenshot kondisi browser saat ini
    """
    driver.get(target_url)

    for i, step in enumerate(steps):
        action = step.get("action")
        logger.info("Step %s: %s", i + 1, step)

        if action == "goto":
            driver.get(step["url"])

        elif action == "fill":
            el = find(driver, step)
            el.clear()
            el.send_keys(step["value"])

        elif action == "click":
            el = find(driver, step)
            el.click()

        elif action == "select":
            el = find(driver, step)
            sel = Select(el)
            if "value" in step:
                sel.select_by_value(step["value"])
            elif "text" in step:
                sel.select_by_visible_text(step["text"])

        elif action == "wait":
            time.sleep(step.get("seconds", 1))

        elif action == "wait_for_element":
            find(driver, step, timeout=step.get("timeout", 15))

        elif action == "screenshot":
            path = os.path.join(screenshot_dir, f"{task_name}_step{i}.png")
            driver.save_screenshot(path)
            logger.info("Screenshot disimpan: %s", path)

        else:
            logger.warning("Aksi tidak dikenal, dilewati: %s", action)

    return "Semua langkah berhasil dijalankan"
