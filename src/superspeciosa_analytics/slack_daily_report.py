from datetime import date
from decimal import Decimal

from superspeciosa_analytics.daily_channel_report import (
    ChannelMetrics,
    DailyChannelReport,
)


ZERO = Decimal("0")


def _money(
    value: Decimal,
) -> str:
    return f"${value:,.2f}"


def _count(
    value: Decimal,
) -> str:
    return f"{value:,.2f}"


def _whole_count(
    value: Decimal,
) -> str:
    return f"{value:,.0f}"


def _multiple(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f}x"


def _date_label(
    value: date,
) -> str:
    return value.strftime(
        "%b %d"
    ).replace(
        " 0",
        " ",
    )


def _percentage_change(
    current: Decimal,
    baseline: Decimal,
) -> Decimal | None:
    if baseline == ZERO:
        return None

    return (
        (current - baseline)
        / baseline
        * Decimal("100")
    )


def _trend(
    current: Decimal,
    baseline: Decimal,
    *,
    higher_is_better: bool | None,
) -> str:
    change = _percentage_change(
        current,
        baseline,
    )

    if change is None:
        return "• n/a"

    if change == ZERO:
        return "⚪ 0.0%"

    rising = (
        change > ZERO
    )

    arrow = (
        "▲"
        if rising
        else "▼"
    )

    if higher_is_better is None:
        return (
            f"{arrow} "
            f"{abs(change):.1f}%"
        )

    good = (
        rising
        if higher_is_better
        else not rising
    )

    indicator = (
        "🟢"
        if good
        else "🔴"
    )

    return (
        f"{indicator} "
        f"{arrow} "
        f"{abs(change):.1f}%"
    )


def _optional_trend(
    current: Decimal | None,
    baseline: Decimal | None,
    *,
    higher_is_better: bool,
) -> str:
    if (
        current is None
        or baseline is None
    ):
        return "• n/a"

    return _trend(
        current,
        baseline,
        higher_is_better=(
            higher_is_better
        ),
    )


def _channel_fields(
    metrics: ChannelMetrics,
) -> list[dict]:
    return [
        {
            "type": "mrkdwn",
            "text": (
                "*Spend*\n"
                f"{_money(metrics.current_spend)} "
                f"{_trend(
                    metrics.current_spend,
                    metrics.baseline_spend,
                    higher_is_better=None,
                )}"
            ),
        },
        {
            "type": "mrkdwn",
            "text": (
                "*Attributed new customers*\n"
                f"{_count(metrics.current_new_customers)} "
                f"{_trend(
                    metrics.current_new_customers,
                    metrics.baseline_new_customers,
                    higher_is_better=True,
                )}"
            ),
        },
        {
            "type": "mrkdwn",
            "text": (
                "*Attributed new-customer revenue*\n"
                f"{_money(metrics.current_new_customer_revenue)} "
                f"{_trend(
                    metrics.current_new_customer_revenue,
                    metrics.baseline_new_customer_revenue,
                    higher_is_better=True,
                )}"
            ),
        },
        {
            "type": "mrkdwn",
            "text": (
                "*New-customer ROAS*\n"
                f"{_multiple(metrics.current_new_customer_roas)} "
                f"{_optional_trend(
                    metrics.current_new_customer_roas,
                    metrics.baseline_new_customer_roas,
                    higher_is_better=True,
                )}"
            ),
        },
        {
            "type": "mrkdwn",
            "text": (
                "*Attributed CAC*\n"
                f"{(
                    _money(metrics.current_cac)
                    if metrics.current_cac is not None
                    else 'n/a'
                )} "
                f"{_optional_trend(
                    metrics.current_cac,
                    metrics.baseline_cac,
                    higher_is_better=False,
                )}"
            ),
        },
    ]


def build_daily_slack_payload(
    report: DailyChannelReport,
) -> dict:
    store = report.store

    weekday = (
        report.current_date.strftime(
            "%A"
        )
    )

    baseline_text = ", ".join(
        _date_label(value)
        for value in report.baseline_dates
    )

    fallback_text = (
        "Super Speciosa daily performance "
        f"for {report.current_date}"
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": (
                    "Super Speciosa | Daily Performance"
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"*{report.current_date}* "
                        f"vs average of prior 4 {weekday}s "
                        f"({baseline_text})"
                    ),
                },
                {
                    "type": "mrkdwn",
                    "text": (
                        "ThoughtMetric: project-default "
                        "Multi-Touch attribution"
                    ),
                },
            ],
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*STORE*",
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "*Product revenue*\n"
                        f"{_money(store.current_product_revenue)} "
                        f"{_trend(
                            store.current_product_revenue,
                            store.baseline_product_revenue,
                            higher_is_better=True,
                        )}"
                    ),
                },
                {
                    "type": "mrkdwn",
                    "text": (
                        "*Qualifying orders*\n"
                        f"{_whole_count(store.current_orders)} "
                        f"{_trend(
                            store.current_orders,
                            store.baseline_orders,
                            higher_is_better=True,
                        )}"
                    ),
                },
                {
                    "type": "mrkdwn",
                    "text": (
                        "*AOV*\n"
                        f"{_money(store.current_aov)} "
                        f"{_trend(
                            store.current_aov,
                            store.baseline_aov,
                            higher_is_better=True,
                        )}"
                    ),
                },
                {
                    "type": "mrkdwn",
                    "text": (
                        "*New customers*\n"
                        f"{_whole_count(store.current_new_customers)} "
                        f"{_trend(
                            store.current_new_customers,
                            store.baseline_new_customers,
                            higher_is_better=True,
                        )}"
                    ),
                },
            ],
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*META*",
            },
        },
        {
            "type": "section",
            "fields": _channel_fields(
                report.meta
            ),
        },
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*EVERFLOW | AFFILIATE*",
            },
        },
        {
            "type": "section",
            "fields": _channel_fields(
                report.everflow
            ),
        },
        {
            "type": "divider",
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "Daily acquisition excludes manual "
                        "spend and blended efficiency. "
                        "ThoughtMetric new-customer credit "
                        "may be fractional under Multi-Touch."
                    ),
                }
            ],
        },
    ]

    return {
        "text": fallback_text,
        "blocks": blocks,
    }