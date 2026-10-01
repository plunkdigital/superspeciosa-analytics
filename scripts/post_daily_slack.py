import json
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_sdk import WebClient


load_dotenv()


payload_path = Path(
    "data/exports/daily_slack_payload.json"
)


channel_id = os.getenv(
    "SLACK_DAILY_CHANNEL_ID"
)

bot_token = os.getenv(
    "SLACK_BOT_TOKEN"
)


if not channel_id:
    raise RuntimeError(
        "SLACK_DAILY_CHANNEL_ID is not configured."
    )

if not bot_token:
    raise RuntimeError(
        "SLACK_BOT_TOKEN is not configured."
    )

if not payload_path.exists():
    raise RuntimeError(
        "Daily Slack payload does not exist."
    )


payload = json.loads(
    payload_path.read_text(
        encoding="utf-8"
    )
)


client = WebClient(
    token=bot_token
)


response = client.chat_postMessage(
    channel=channel_id,
    text=payload["text"],
    blocks=payload["blocks"],
)


print(
    "Posted daily Slack report."
)

print(
    "Channel:",
    response["channel"],
)

print(
    "Timestamp:",
    response["ts"],
)