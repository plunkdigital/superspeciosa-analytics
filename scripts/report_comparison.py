import argparse
from datetime import date, timedelta
from decimal import Decimal

from superspeciosa_analytics.data_quality import (
    get_meta_coverage,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting_compare import (
    CountComparison,
    MetricComparison,
    get_commercial_comparison,
    get_commercial_comparison_for_periods,
)
from superspeciosa_analytics.reporting_presets import (
    ComparisonPreset,
    resolve_comparison_preset,
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def money(value: Decimal) -> str:
    return f"${value:,.2f}"


def percentage(
    value: Decimal | None,
) -> str:
    if value is None:
        return "n/a"

    return f"{value:+.1f}%"


def metric_line(
    label: str,
    comparison: MetricComparison,
    *,
    formatter,
) -> None:
    print(
        f"{label:<28}"
        f"{formatter(comparison.current):>16}"
        f"{formatter(comparison.previous):>16}"
        f"{percentage(comparison.percentage_change):>12}"
    )


def count_line(
    label: str,
    comparison: CountComparison,
) -> None:
    print(
        f"{label:<28}"
        f"{comparison.current:>16,}"
        f"{comparison.previous:>16,}"
        f"{percentage(comparison.percentage_change):>12}"
    )


parser = argparse.ArgumentParser()

parser.add_argument(
    "--preset",
    choices=[
        preset.value
        for preset in ComparisonPreset
    ],
    help=(
        "Comparison preset: yesterday, "
        "last7, or mtd."
    ),
)

parser.add_argument(
    "--as-of",
    type=parse_date,
    help=(
        "Exclusive end date for a preset. "
        "Defaults to today's business date."
    ),
)

parser.add_argument(
    "--start",
    type=parse_date,
    help="Explicit current-period start.",
)

parser.add_argument(
    "--end",
    type=parse_date,
    help="Explicit current-period end exclusive.",
)

args = parser.parse_args()


if args.preset:
    if (
        args.start is not None
        or args.end is not None
    ):
        parser.error(
            "Do not combine --preset with "
            "--start or --end."
        )

    periods = resolve_comparison_preset(
        args.preset,
        as_of=args.as_of,
    )

else:
    if (
        args.start is None
        or args.end is None
    ):
        parser.error(
            "Provide either --preset or both "
            "--start and --end."
        )


with SessionLocal() as session:
    if args.preset:
        report = (
            get_commercial_comparison_for_periods(
                session,
                current_start=(
                    periods.current_start
                ),
                current_end=(
                    periods.current_end
                ),
                previous_start=(
                    periods.previous_start
                ),
                previous_end=(
                    periods.previous_end
                ),
            )
        )

    else:
        report = get_commercial_comparison(
            session,
            start=args.start,
            end=args.end,
        )

    current_meta_coverage = get_meta_coverage(
        session,
        start=report.current_start,
        end=(
            report.current_end
            - timedelta(days=1)
        ),
    )

    previous_meta_coverage = get_meta_coverage(
        session,
        start=report.previous_start,
        end=(
            report.previous_end
            - timedelta(days=1)
        ),
    )

    marketing_comparison_complete = (
        current_meta_coverage.complete_daily_coverage
        and previous_meta_coverage.complete_daily_coverage
    )


print()
print("SUPER SPECIOSA PERIOD COMPARISON")
print("=" * 76)

print(
    "Current:  "
    f"{report.current_start} "
    f"through {report.current_end} exclusive"
)

print(
    "Previous: "
    f"{report.previous_start} "
    f"through {report.previous_end} exclusive"
)

print()
print(
    f"{'Metric':<28}"
    f"{'Current':>16}"
    f"{'Previous':>16}"
    f"{'Change':>12}"
)

print("-" * 76)


metric_line(
    "Product revenue",
    report.product_revenue,
    formatter=money,
)

count_line(
    "Qualifying orders",
    report.qualifying_orders,
)

metric_line(
    "Average order value",
    report.average_order_value,
    formatter=money,
)

count_line(
    "New customers",
    report.new_customers,
)

metric_line(
    "New customer revenue",
    report.new_customer_revenue,
    formatter=money,
)

count_line(
    "Returning customers",
    report.returning_customers,
)

metric_line(
    "Returning revenue",
    report.returning_customer_revenue,
    formatter=money,
)

if marketing_comparison_complete:
    metric_line(
        "Meta spend",
        report.meta_spend,
        formatter=money,
    )

    metric_line(
        "Manual spend",
        report.manual_spend,
        formatter=money,
    )

    metric_line(
        "Total marketing spend",
        report.total_marketing_spend,
        formatter=money,
    )

    if (
        report.blended_marketing_efficiency
        is not None
    ):
        metric_line(
            "Blended efficiency",
            report.blended_marketing_efficiency,
            formatter=lambda value: (
                f"{value:.2f}x"
            ),
        )

    if (
        report.blended_new_customer_acquisition_cost
        is not None
    ):
        metric_line(
            "Blended new-customer CAC",
            report.blended_new_customer_acquisition_cost,
            formatter=money,
        )

else:
    print()
    print(
        "Marketing comparison omitted: "
        "Meta coverage is incomplete."
    )


print()
print("DATA COVERAGE")
print("-" * 76)

print(
    "Current Meta:",
    (
        "complete"
        if current_meta_coverage.complete_daily_coverage
        else (
            f"incomplete "
            f"({current_meta_coverage.rows_present}/"
            f"{current_meta_coverage.expected_days} days)"
        )
    ),
)

print(
    "Previous Meta:",
    (
        "complete"
        if previous_meta_coverage.complete_daily_coverage
        else (
            f"incomplete "
            f"({previous_meta_coverage.rows_present}/"
            f"{previous_meta_coverage.expected_days} days)"
        )
    ),
)