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
from superspeciosa_analytics.reporting_time import (
    get_reporting_timezone,
)
from superspeciosa_analytics.source_freshness import (
    get_source_freshness,
)
from superspeciosa_analytics.reporting_compare import (
    get_commercial_comparison_for_periods,
)
from superspeciosa_analytics.reporting_presets import (
    ComparisonPreset,
    current_business_date,
    resolve_comparison_preset,
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

'/analytics yesterday'
'/analytics last7'
'/analytics mtd'

You can also mention the bot:

`@Super Speciosa Analytics daily`
`@Super Speciosa Analytics freshness`
""".strip()

def _percentage(
    value,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:+.1f}%"

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

    if request in {
        "yesterday",
        "yday",
    }:
        return build_period_message(
            ComparisonPreset.YESTERDAY
        )

    if request in {
        "last7",
        "last 7",
        "week",
    }:
        return build_period_message(
            ComparisonPreset.LAST_7_DAYS
        )

    if request in {
        "mtd",
        "month",
        "month to date",
    }:
        return build_period_message(
            ComparisonPreset.MONTH_TO_DATE
        )

    return (
        "I don't recognise that command yet.\n\n"
        + HELP_TEXT
    )

def build_period_message(
    preset: ComparisonPreset,
) -> str:
    as_of = current_business_date()

    periods = resolve_comparison_preset(
        preset,
        as_of=as_of,
    )

    with SessionLocal() as session:
        report = get_commercial_comparison_for_periods(
            session,
            current_start=periods.current_start,
            current_end=periods.current_end,
            previous_start=periods.previous_start,
            previous_end=periods.previous_end,
        )

    lines = [
        "*Super Speciosa Commercial Comparison*",
        "",
        (
            f"*Current:* "
            f"{report.current_start} through "
            f"{report.current_end} exclusive"
        ),
        (
            f"*Previous:* "
            f"{report.previous_start} through "
            f"{report.previous_end} exclusive"
        ),
        "",
        (
            "*Product revenue:* "
            f"${report.product_revenue.current:,.2f} "
            f"({_percentage(report.product_revenue.percentage_change)})"
        ),
        (
            "*Qualifying orders:* "
            f"{report.qualifying_orders.current:,} "
            f"({_percentage(report.qualifying_orders.percentage_change)})"
        ),
        (
            "*AOV:* "
            f"${report.average_order_value.current:,.2f} "
            f"({_percentage(report.average_order_value.percentage_change)})"
        ),
        (
            "*New customers:* "
            f"{report.new_customers.current:,} "
            f"({_percentage(report.new_customers.percentage_change)})"
        ),
        (
            "*Marketing spend:* "
            f"${report.total_marketing_spend.current:,.2f} "
            f"({_percentage(report.total_marketing_spend.percentage_change)})"
        ),
    ]

    if (
        report.blended_marketing_efficiency
        is not None
    ):
        lines.append(
            "*Blended efficiency:* "
            f"{report.blended_marketing_efficiency.current:.2f}x "
            f"({_percentage(report.blended_marketing_efficiency.percentage_change)})"
        )

    if (
        report.blended_new_customer_acquisition_cost
        is not None
    ):
        lines.append(
            "*New-customer CAC:* "
            f"${report.blended_new_customer_acquisition_cost.current:,.2f} "
            f"({_percentage(report.blended_new_customer_acquisition_cost.percentage_change)})"
        )

    return "\n".join(lines)


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