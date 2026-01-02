import asyncio
import json
import os

import websockets
from dotenv import load_dotenv
from Slack_bot.models import lists
from Slack_bot.log_m.log import incident_log
from Slack_bot.slack_m.slack_sender import default_blocks, restored_blocks
from Slack_bot.utils.logging import write_log

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(ENV_PATH)

WEBSOCKET_URI = os.getenv("WEBSOCKET_URI")
if not WEBSOCKET_URI:
    flask_address = os.getenv("FLASK_SERVER_ADDRESS", "ws://127.0.0.1")
    flask_port = os.getenv("FLASK_SERVER_PORT", "5002")
    WEBSOCKET_URI = f"{flask_address}:{flask_port}"

def _parse_incident(message):
    try:
        return json.loads(message)
    except json.JSONDecodeError as exc:
        incident_log(f"JSON decode error: {exc}")
        write_log("IncidentBot", f"JSON decode error: {exc}")
        return None


def _build_incident_object(incident):
    incident_id = incident.get("id")
    service = incident.get("service")
    status = incident.get("status")
    detail = incident.get("detail", "")
    occurred_at = incident.get("occurred_at")
    restored_at = incident.get("restored_at")
    logs = []
    return lists(incident_id, service, status, detail, occurred_at, restored_at, logs)


async def connect_to_websocket():
    try:
        async with websockets.connect(WEBSOCKET_URI) as websocket:
            incident_log(f"Connected to WebSocket server at {WEBSOCKET_URI}")
            write_log("IncidentBot", f"Connected to WebSocket server at {WEBSOCKET_URI}")

            while True:
                message = await websocket.recv()
                incident_log(f"Received message: {message}")

                data = _parse_incident(message)
                if not data:
                    continue

                incident_update = data.get("incident_update")
                if not incident_update:
                    continue

                incident = incident_update.get("incident", {})
                incident_object = _build_incident_object(incident)

                status = incident_object.get_status()
                if status and status.lower() == "restored":
                    restored_blocks(incident_object)
                else:
                    default_blocks(incident_object)

    except websockets.exceptions.ConnectionClosed as exc:
        incident_log(f"WebSocket connection closed unexpectedly: {exc}")
        write_log("IncidentBot", f"WebSocket connection closed unexpectedly: {exc}")
    except Exception as exc:
        incident_log(f"Unexpected error: {exc}")
        write_log("IncidentBot", f"Unexpected error: {exc}")

async def main():
    print("Started WebSocket client.")
    write_log("IncidentBot", "Service started")
    await connect_to_websocket()

if __name__ == "__main__":
    asyncio.run(main())

