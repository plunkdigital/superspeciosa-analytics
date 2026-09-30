import argparse
from datetime import date, timedelta
from decimal import Decimal

from superspeciosa_analytics.reporting_presets import (
    current_business_date,
)
from superspeciosa_analytics.thoughtmetric import (
    get_channel_performance,
)


ZERO = Decimal("0")


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def decimal_value(value) -> Decimal:
    if value is None:
        return ZERO

    return Decimal(
        str(value)
    )


parser = argparse.ArgumentParser()

parser.add_argument(
    "--date",
    type=parse_date,
    help=(
        "Business date to inspect. "
        "Defaults to yesterday."
    ),
)

args = parser.parse_args()


report_date = (
    args.date
    if args.date is not None
    else (
        current_business_date()
        - timedelta(days=1)
    )
)


data = get_channel_performance(
    start=report_date,
    end=report_date,
)


rows = data.get(
    "total",
    [],
)


print()
print("THOUGHTMETRIC CONNECTION CHECK")
print("=" * 72)

print(
    "Report date:",
    report_date,
)

print(
    "Attribution model parameter:",
    "omitted (project default)",
)

print(
    "Channels returned:",
    len(rows),
)

print()


total_orders = ZERO
total_new_customer_orders = ZERO
total_sales = ZERO


for row in rows:
    channel = str(
        row.get(
            "channel",
            "unknown",
        )
    )

    orders = decimal_value(
        row.get(
            "orders"
        )
    )

    new_customer_orders = (
        decimal_value(
            row.get(
                "new_customer_orders"
            )
        )
    )

    new_customer_sales = (
        decimal_value(
            row.get(
                "new_customer_total_sales"
            )
        )
    )

    total_channel_sales = (
        decimal_value(
            row.get(
                "total_sales"
            )
        )
    )

    converted_spend = (
        decimal_value(
            row.get(
                "converted_spend"
            )
        )
    )

    cost_per_new_customer = (
        row.get(
            "cost_per_new_customer_order"
        )
    )

    total_orders += orders

    total_new_customer_orders += (
        new_customer_orders
    )

    total_sales += total_channel_sales

    print("-" * 72)

    print(
        "Channel:",
        channel,
    )

    print(
        "Orders:",
        orders,
    )

    print(
        "New customer orders:",
        new_customer_orders,
    )

    print(
        "New customer sales:",
        f"${new_customer_sales:,.2f}",
    )

    print(
        "Attributed total sales:",
        f"${total_channel_sales:,.2f}",
    )

    print(
        "ThoughtMetric converted spend:",
        f"${converted_spend:,.2f}",
    )

    print(
        "ThoughtMetric new-customer CAC:",
        cost_per_new_customer,
    )


print()
print("=" * 72)
print("ATTRIBUTED TOTALS")
print("-" * 72)

print(
    "Orders:",
    total_orders,
)

print(
    "New customer orders:",
    total_new_customer_orders,
)

print(
    "Attributed total sales:",
    f"${total_sales:,.2f}",
)

print()
print(
    "ThoughtMetric connection check passed."
)