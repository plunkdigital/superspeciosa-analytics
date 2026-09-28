import argparse
from datetime import date
from decimal import Decimal

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting_compare import (
    CountComparison,
    MetricComparison,
    get_commercial_comparison,
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
    "--start",
    required=True,
    type=parse_date,
    help="Current-period start inclusive",
)

parser.add_argument(
    "--end",
    required=True,
    type=parse_date,
    help="Current-period end exclusive",
)

args = parser.parse_args()


with SessionLocal() as session:
    report = get_commercial_comparison(
        session,
        start=args.start,
        end=args.end,
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