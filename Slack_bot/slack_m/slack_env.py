# 환경 변수 로드
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

from slack_sdk import WebClient

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(ENV_PATH)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SLACK_ISSUE_CHANNEL_ID = os.getenv("SLACK_ISSUE_CHANNEL_ID")
# Slack 클라이언트 초기화
client = WebClient(token=SLACK_BOT_TOKEN)
