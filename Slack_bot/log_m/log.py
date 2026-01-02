from datetime import datetime
import os

DEFAULT_LOG_DIR = os.getenv("BOT_LOG_DIR", "/home/Ubicomp/bot/total_log")


def _append_line(log_path, message):
    now = datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
    with open(log_path, "a") as log_txt:
        print(f"{now} | {message}", file=log_txt)


def log(message):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "total_log"))
    os.makedirs(base_dir, exist_ok=True)
    log_path = os.path.join(base_dir, "slack_log.txt")
    _append_line(log_path, message)


def incident_log(message, log_dir=None):
    base_dir = log_dir or DEFAULT_LOG_DIR
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "total_log"))
        os.makedirs(base_dir, exist_ok=True)
    log_path = os.path.join(base_dir, "incident_log.txt")
    _append_line(log_path, message)
