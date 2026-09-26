import argparse
from datetime import UTC, datetime, time
from decimal import Decimal

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting import (
    get_commercial_summary,
)


def parse_date(value: str) -> datetime:
    parsed = datetime.strptime(
        value,
        "%Y-%m-%d",
    ).date()

    return datetime.combine(
        parsed,
        time.min,
        tzinfo=UTC,
    )


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

start = parse_date(args.start)
end = parse_date(args.end)


with SessionLocal() as session:
    report = get_commercial_summary(
        session,
        start=start,
        end=end,
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
    "Refund events:",
    report.refund_events,
)

print(
    "Cash refunded:",
    money(
        report.total_cash_refunded
    ),
)

print(
    "Attributed product refunds:",
    money(
        report.product_refund_amount
    ),
)

print(
    "Attributed shipping refunds:",
    money(
        report.shipping_refund_amount
    ),
)

print(
    "Attributed tax refunds:",
    money(
        report.tax_refund_amount
    ),
)