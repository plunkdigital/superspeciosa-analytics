import os
import re
from datetime import datetime

from slack_bolt import App

from superspeciosa_analytics.daily_brief import (
    DailyBriefIncompleteDataError,
    build_daily_brief,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting_presets import (
    current_business_date,
)
from superspeciosa_analytics.reporting_time import (
    get_reporting_timezone,
)
from superspeciosa_analytics.source_freshness import (
    get_source_freshness,
)


HELP_TEXT = """
*Super Speciosa Analytics*

Available commands:

`/analytics daily`
Current daily commercial brief.

`/analytics freshness`
Latest ingestion/check time for each source.

`/analytics help`
Show this help.

You can also mention the bot:

`@Super Speciosa Analytics daily`
`@Super Speciosa Analytics freshness`
""".strip()


def _normalize_request(
    value: str,
) -> str:
    value = re.sub(
        r"<@[A-Z0-9]+>",
        "",
        value,
    )

    return value.strip().lower()


def _allowed_channel_ids() -> set[str]:
    raw = os.getenv(
        "SLACK_ALLOWED_CHANNEL_IDS",
        "",
    )

    return {
        value.strip()
        for value in raw.split(",")
        if value.strip()
    }


def _channel_allowed(
    channel_id: str | None,
) -> bool:
    allowed = _allowed_channel_ids()

    if not allowed:
        return True

    if channel_id is None:
        return False

    return channel_id in allowed


def _freshness_time(
    value: datetime | None,
) -> str:
    if value is None:
        return "never imported"

    local = value.astimezone(
        get_reporting_timezone()
    )

    return local.strftime(
        "%Y-%m-%d %H:%M %Z"
    )


def build_freshness_message() -> str:
    with SessionLocal() as session:
        freshness = get_source_freshness(
            session
        )

    lines = [
        "*Super Speciosa Data Freshness*",
        "",
        (
            "*Shopify:* "
            + _freshness_time(
                freshness.shopify
            )
        ),
        (
            "*Meta:* "
            + _freshness_time(
                freshness.meta
            )
        ),
        (
            "*Everflow:* "
            + _freshness_time(
                freshness.everflow
            )
        ),
        (
            "*Manual spend:* "
            + _freshness_time(
                freshness.manual_spend
            )
        ),
    ]

    return "\n".join(lines)


def build_daily_message() -> str:
    as_of = current_business_date()

    with SessionLocal() as session:
        return build_daily_brief(
            session,
            as_of=as_of,
            require_complete_marketing=True,
        )


def handle_reporting_request(
    text: str,
) -> str:
    request = _normalize_request(
        text
    )

    if request in {
        "",
        "help",
    }:
        return HELP_TEXT

    if request in {
        "daily",
        "brief",
        "daily brief",
    }:
        return build_daily_message()

    if request in {
        "freshness",
        "status",
        "data status",
    }:
        return build_freshness_message()

    return (
        "I don't recognise that command yet.\n\n"
        + HELP_TEXT
    )


def create_slack_app() -> App:
    bot_token = os.getenv(
        "SLACK_BOT_TOKEN"
    )

    if not bot_token:
        raise RuntimeError(
            "SLACK_BOT_TOKEN is not configured."
        )

    app = App(
        token=bot_token
    )

    @app.command("/analytics")
    def handle_analytics_command(
        ack,
        command,
        respond,
        logger,
    ):
        ack()

        channel_id = command.get(
            "channel_id"
        )

        if not _channel_allowed(
            channel_id
        ):
            respond(
                "This channel is not authorised "
                "for Super Speciosa reporting."
            )
            return

        try:
            response = (
                handle_reporting_request(
                    command.get(
                        "text",
                        "",
                    )
                )
            )

        except DailyBriefIncompleteDataError as exc:
            response = (
                ":warning: Daily reporting data "
                "is incomplete.\n"
                f"{exc}"
            )

        except Exception:
            logger.exception(
                "Slack reporting command failed"
            )

            response = (
                ":warning: The analytics request "
                "failed. Check the reporting "
                "service logs."
            )

        respond(response)

    @app.event("app_mention")
    def handle_app_mention(
        event,
        say,
        logger,
    ):
        channel_id = event.get(
            "channel"
        )

        if not _channel_allowed(
            channel_id
        ):
            say(
                "This channel is not authorised "
                "for Super Speciosa reporting."
            )
            return

        try:
            response = (
                handle_reporting_request(
                    event.get(
                        "text",
                        "",
                    )
                )
            )

        except DailyBriefIncompleteDataError as exc:
            response = (
                ":warning: Daily reporting data "
                "is incomplete.\n"
                f"{exc}"
            )

        except Exception:
            logger.exception(
                "Slack app mention failed"
            )

            response = (
                ":warning: The analytics request "
                "failed. Check the reporting "
                "service logs."
            )

        say(response)

    return app