from datetime import datetime
import os

DEFAULT_LOG_DIR = os.getenv("BOT_LOG_DIR", "/home/Ubicomp/bot/total_log")
DEFAULT_LOG_FILE = "total_services_log.txt"


def _resolve_log_path(log_dir, filename):
    base_dir = log_dir or DEFAULT_LOG_DIR
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "total_log")
        )
        os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, filename)


def write_log(source, message, log_dir=None):
    log_path = _resolve_log_path(log_dir, DEFAULT_LOG_FILE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as log_file:
        log_file.write(f"[{now}] [{source}] {message}\n")
