import argparse
from datetime import date
from decimal import Decimal

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting import (
    get_commercial_summary,
)
from superspeciosa_analytics.reporting_time import (
    reporting_date_range_to_utc,
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def money(value: Decimal) -> str:
    return f"${value:,.2f}"


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    help="Start date inclusive, YYYY-MM-DD",
)

parser.add_argument(
    "--end",
    required=True,
    help="End date exclusive, YYYY-MM-DD",
)

args = parser.parse_args()

report_start_date = parse_date(
    args.start
)

report_end_date = parse_date(
    args.end
)

start, end = reporting_date_range_to_utc(
    start=report_start_date,
    end=report_end_date,
)


with SessionLocal() as session:
    report = get_commercial_summary(
        session,
        start=start,
        end=end,
        report_start_date=(
            report_start_date
        ),
        report_end_date=(
            report_end_date
        ),
    )


print()
print("SUPER SPECIOSA COMMERCIAL SUMMARY")
print("=" * 60)

print(
    f"Period: {args.start} through "
    f"{args.end} exclusive"
)


print()
print("SALES")
print("-" * 60)

print(
    "Product revenue:",
    money(report.product_revenue),
)

print(
    "Qualifying orders:",
    report.qualifying_orders,
)

print(
    "Average order value:",
    money(report.average_order_value),
)


print()
print("CUSTOMER MIX")
print("-" * 60)

print(
    "New customers:",
    report.new_customers,
)

print(
    "New customer orders:",
    report.new_customer_orders,
)

print(
    "New customer revenue:",
    money(
        report.new_customer_revenue
    ),
)

print(
    "Returning customers:",
    report.returning_customers,
)

print(
    "Returning customer orders:",
    report.returning_customer_orders,
)

print(
    "Returning customer revenue:",
    money(
        report.returning_customer_revenue
    ),
)


print()
print("UNRESOLVED CUSTOMER IDENTITY")
print("-" * 60)

print(
    "Orders:",
    report.unresolved_orders,
)

print(
    "Revenue:",
    money(
        report.unresolved_revenue
    ),
)


print()
print("REFUNDS PROCESSED DURING PERIOD")
print("-" * 60)

print(
    "Cash refund events:",
    report.refund_events,
)

print(
    "Cash refunded:",
    money(
        report.total_cash_refunded
    ),
)

print(
    "Refund component allocation:",
    "not reported pending reconciliation",
)

print()
print("MARKETING")
print("-" * 60)

print(
    "Meta spend:",
    money(report.meta_spend),
)

print(
    "Manual spend:",
    money(report.manual_spend),
)

print(
    "Everflow payout:",
    money(
        report.everflow_payout
    ),
)

print(
    "Total marketing spend:",
    money(
        report.total_marketing_spend
    ),
)


print()
print("EFFICIENCY")
print("-" * 60)

if (
    report.blended_marketing_efficiency
    is None
):
    print(
        "Blended marketing efficiency: n/a"
    )
else:
    print(
        "Blended marketing efficiency:",
        f"{report.blended_marketing_efficiency:.2f}x",
    )

if (
    report.blended_new_customer_acquisition_cost
    is None
):
    print(
        "Blended new-customer CAC: n/a"
    )
else:
    print(
        "Blended new-customer CAC:",
        money(
            report.blended_new_customer_acquisition_cost
        ),
    )