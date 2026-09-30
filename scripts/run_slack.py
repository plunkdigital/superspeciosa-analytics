import os

from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import (
    SocketModeHandler,
)

from superspeciosa_analytics.slack_app import (
    create_slack_app,
)


load_dotenv()


app_token = os.getenv(
    "SLACK_APP_TOKEN"
)

if not app_token:
    raise RuntimeError(
        "SLACK_APP_TOKEN is not configured."
    )


app = create_slack_app()


print()
print("SUPER SPECIOSA SLACK APP")
print("=" * 60)
print("Starting Socket Mode...")
print()


SocketModeHandler(
    app,
    app_token,
).start()