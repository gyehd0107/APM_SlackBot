import time
import schedule
from datetime import datetime
from Slack_bot.send_m.send_report import send_report, KST
from Slack_bot.utils.logging import write_log

def job():
    """매일 실행되지만, 1일인 경우 월간 보고서를 전송"""
    if datetime.now(KST).day == 1:
        write_log("SlackBot", "Triggering monthly report")
        send_report("Monthly", months_offset=1)

def start_scheduler():
    # 매일 09:01:00에 일간 보고 전송
    schedule.every().day.at("21:46:30").do(lambda: log_and_send("Daily", days_offset=1))

    # 매주 월요일 09:01:20에 주간 보고 전송
    schedule.every().monday.at("09:01:20").do(lambda: log_and_send("Weekly", days_offset=7))

    # 매일 09:01:50에 실행되지만, 1일이면 월간 보고 전송
    schedule.every().day.at("09:01:50").do(job)

    print("Scheduler started.")
    write_log("SlackBot", "Scheduler started")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        write_log("SlackBot", "Scheduler manually stopped")

def log_and_send(report_type, **kwargs):
    try:
        write_log("SlackBot", f"Sending {report_type} report")
        send_report(report_type, **kwargs)
        write_log("SlackBot", f"{report_type} report sent successfully")
    except Exception as e:
        write_log("SlackBot", f"ERROR while sending {report_type} report: {str(e)}")

if __name__ == "__main__":
    write_log("SlackBot", "Service started")
    start_scheduler()
