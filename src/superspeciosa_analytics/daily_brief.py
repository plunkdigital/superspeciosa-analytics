from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from superspeciosa_analytics.data_quality import (
    get_everflow_coverage,
    get_meta_coverage,
)
from superspeciosa_analytics.reporting_compare import (
    CommercialComparison,
    get_commercial_comparison_for_periods,
)
from superspeciosa_analytics.reporting_presets import (
    ComparisonPreset,
    resolve_comparison_preset,
)
from superspeciosa_analytics.report_observations import (
    build_observations,
)
from superspeciosa_analytics.reporting_time import (
    get_reporting_timezone,
)
from superspeciosa_analytics.source_freshness import (
    get_source_freshness,
)

class DailyBriefIncompleteDataError(
    RuntimeError
):
    pass

def _money(value: Decimal) -> str:
    return f"${value:,.2f}"


def _count(value: int) -> str:
    return f"{value:,}"


def _percentage(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:+.1f}%"


def _multiple(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:.2f}x"


def _change_text(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return _percentage(value)

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


def _marketing_coverage_complete(
    session: Session,
    comparison: CommercialComparison,
) -> bool:
    current_end = (
        comparison.current_end
        - timedelta(days=1)
    )

    previous_end = (
        comparison.previous_end
        - timedelta(days=1)
    )

    current_meta = get_meta_coverage(
        session,
        start=comparison.current_start,
        end=current_end,
    )

    previous_meta = get_meta_coverage(
        session,
        start=comparison.previous_start,
        end=previous_end,
    )

    current_everflow = (
        get_everflow_coverage(
            session,
            start=comparison.current_start,
            end=current_end,
        )
    )

    previous_everflow = (
        get_everflow_coverage(
            session,
            start=comparison.previous_start,
            end=previous_end,
        )
    )

    return (
        current_meta.complete_daily_coverage
        and previous_meta.complete_daily_coverage
        and current_everflow.complete_daily_coverage
        and previous_everflow.complete_daily_coverage
    )


def _get_comparison(
    session: Session,
    *,
    preset: ComparisonPreset,
    as_of: date,
) -> CommercialComparison:
    periods = resolve_comparison_preset(
        preset,
        as_of=as_of,
    )

    return get_commercial_comparison_for_periods(
        session,
        current_start=periods.current_start,
        current_end=periods.current_end,
        previous_start=periods.previous_start,
        previous_end=periods.previous_end,
    )


def _headline_section(
    title: str,
    comparison: CommercialComparison,
    *,
    marketing_complete: bool,
) -> list[str]:
    lines = []

    lines.append(title)
    lines.append("-" * 72)

    lines.append(
        "Product revenue: "
        f"{_money(comparison.product_revenue.current)} "
        f"({_change_text(comparison.product_revenue.percentage_change)})"
    )

    lines.append(
        "Qualifying orders: "
        f"{_count(comparison.qualifying_orders.current)} "
        f"({_change_text(comparison.qualifying_orders.percentage_change)})"
    )

    lines.append(
        "AOV: "
        f"{_money(comparison.average_order_value.current)} "
        f"({_change_text(comparison.average_order_value.percentage_change)})"
    )

    lines.append(
        "New customers: "
        f"{_count(comparison.new_customers.current)} "
        f"({_change_text(comparison.new_customers.percentage_change)})"
    )

    if marketing_complete:
        lines.append(
            "Marketing spend: "
            f"{_money(comparison.total_marketing_spend.current)} "
            f"({_change_text(comparison.total_marketing_spend.percentage_change)})"
        )

        if (
            comparison.blended_marketing_efficiency
            is not None
        ):
            lines.append(
                "Blended efficiency: "
                f"{_multiple(comparison.blended_marketing_efficiency.current)} "
                f"({_change_text(comparison.blended_marketing_efficiency.percentage_change)})"
            )

        if (
            comparison.blended_new_customer_acquisition_cost
            is not None
        ):
            lines.append(
                "New-customer CAC: "
                f"{_money(comparison.blended_new_customer_acquisition_cost.current)} "
                f"({_change_text(comparison.blended_new_customer_acquisition_cost.percentage_change)})"
            )

    else:
        lines.append(
            "Marketing: omitted because source "
            "coverage is incomplete."
        )

    return lines


def build_daily_brief(
    session: Session,
    *,
    as_of: date,
    require_complete_marketing: bool = False,
) -> str:
    yesterday = _get_comparison(
        session,
        preset=ComparisonPreset.YESTERDAY,
        as_of=as_of,
    )

    last_7 = _get_comparison(
        session,
        preset=ComparisonPreset.LAST_7_DAYS,
        as_of=as_of,
    )

    month_to_date = _get_comparison(
        session,
        preset=ComparisonPreset.MONTH_TO_DATE,
        as_of=as_of,
    )

    yesterday_marketing_complete = (
        _marketing_coverage_complete(
            session,
            yesterday,
        )
    )

    last_7_marketing_complete = (
        _marketing_coverage_complete(
            session,
            last_7,
        )
    )

    mtd_marketing_complete = (
        _marketing_coverage_complete(
            session,
            month_to_date,
        )
    )

    if require_complete_marketing:
        incomplete_periods = []

        if not yesterday_marketing_complete:
            incomplete_periods.append(
                "yesterday"
            )

        if not last_7_marketing_complete:
            incomplete_periods.append(
                "last 7 days"
            )

        if not mtd_marketing_complete:
            incomplete_periods.append(
                "month to date"
            )

        if incomplete_periods:
            raise DailyBriefIncompleteDataError(
                "Incomplete marketing source "
                "coverage for: "
                + ", ".join(
                    incomplete_periods
                )
            )

    observations = build_observations(
        yesterday=yesterday,
        last_7=last_7,
        month_to_date=month_to_date,
        yesterday_marketing_complete=(
            yesterday_marketing_complete
        ),
        last_7_marketing_complete=(
            last_7_marketing_complete
        ),
        mtd_marketing_complete=(
            mtd_marketing_complete
        ),
    )

    freshness = get_source_freshness(
        session
    )

    completed_through = (
        as_of
        - timedelta(days=1)
    )

    lines = [
        "",
        "SUPER SPECIOSA DAILY BRIEF",
        "=" * 72,
        (
            f"As of {as_of} exclusive "
            f"(completed through {completed_through})"
        ),
        "",
    ]

    lines.extend(
        _headline_section(
            "YESTERDAY VS PREVIOUS DAY",
            yesterday,
            marketing_complete=(
                yesterday_marketing_complete
            ),
        )
    )

    if yesterday_marketing_complete:
        lines.extend(
            [
                "",
                "Yesterday marketing mix:",
                (
                    f"  Meta: "
                    f"{_money(yesterday.current.meta_spend)}"
                ),
                (
                    f"  Everflow payout: "
                    f"{_money(yesterday.current.everflow_payout)}"
                ),
                (
                    f"  Manual: "
                    f"{_money(yesterday.current.manual_spend)}"
                ),
            ]
        )

    lines.append("")

    lines.extend(
        _headline_section(
            "LAST 7 DAYS VS PREVIOUS 7 DAYS",
            last_7,
            marketing_complete=(
                last_7_marketing_complete
            ),
        )
    )

    lines.append("")

    lines.extend(
        _headline_section(
            "MONTH TO DATE VS EQUIVALENT PRIOR MONTH",
            month_to_date,
            marketing_complete=(
                mtd_marketing_complete
            ),
        )
    )

    lines.extend(
        [
            "",
            "OBSERVATIONS",
            "-" * 72,
        ]
    )

    for observation in observations:
        lines.append(
            f"- {observation}"
        )

    lines.extend(
        [
            "",
            "DATA STATUS",
            "-" * 72,
            (
                "Yesterday marketing sources: "
                + (
                    "complete"
                    if yesterday_marketing_complete
                    else "incomplete"
                )
            ),
            (
                "Last 7 marketing sources: "
                + (
                    "complete"
                    if last_7_marketing_complete
                    else "incomplete"
                )
            ),
            (
                "MTD marketing sources: "
                + (
                    "complete"
                    if mtd_marketing_complete
                    else "incomplete"
                )
            ),
            "",
            "SOURCE FRESHNESS",
            "-" * 72,
            (
                "Shopify: "
                + _freshness_time(
                    freshness.shopify
                )
            ),
            (
                "Meta: "
                + _freshness_time(
                    freshness.meta
                )
            ),
            (
                "Everflow: "
                + _freshness_time(
                    freshness.everflow
                )
            ),
            (
                "Manual spend: "
                + _freshness_time(
                    freshness.manual_spend
                )
            ),
        ]
    )

    return "\n".join(lines)