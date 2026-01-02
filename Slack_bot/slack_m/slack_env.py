# ?섍꼍 蹂??濡쒕뱶
import os

from dotenv import load_dotenv
from slack_sdk import WebClient

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(ENV_PATH)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
SLACK_ISSUE_CHANNEL_ID = os.getenv("SLACK_ISSUE_CHANNEL_ID")
# Slack ?대씪?댁뼵??珥덇린??client = WebClient(token=SLACK_BOT_TOKEN)

