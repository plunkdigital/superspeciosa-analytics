import os
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
    MetaDailySpend,
    ThoughtMetricDailyChannel,
)


REPORT_DATE = date(
    2026,
    9,
    29,
)


def keys_from_env(
    name: str,
) -> set[str]:
    return {
        value.strip()
        for value in os.getenv(
            name,
            "",
        ).split(",")
        if value.strip()
    }


meta_keys = keys_from_env(
    "THOUGHTMETRIC_META_CHANNEL_KEYS"
)

everflow_keys = keys_from_env(
    "THOUGHTMETRIC_EVERFLOW_CHANNEL_KEYS"
)


with SessionLocal() as session:
    rows = session.scalars(
        select(
            ThoughtMetricDailyChannel
        )
        .where(
            ThoughtMetricDailyChannel.report_date
            == REPORT_DATE
        )
        .order_by(
            ThoughtMetricDailyChannel.channel_key
        )
    ).all()

    meta_spend = session.scalar(
        select(
            func.sum(
                MetaDailySpend.spend
            )
        )
        .where(
            MetaDailySpend.report_date
            == REPORT_DATE
        )
    ) or Decimal("0")

    everflow_payout = session.scalar(
        select(
            func.sum(
                EverflowDailyPerformance.payout
            )
        )
        .where(
            EverflowDailyPerformance.report_date
            == REPORT_DATE
        )
    ) or Decimal("0")


meta_new_customers = sum(
    (
        row.new_customer_orders
        for row in rows
        if row.channel_key in meta_keys
    ),
    Decimal("0"),
)

everflow_new_customers = sum(
    (
        row.new_customer_orders
        for row in rows
        if row.channel_key in everflow_keys
    ),
    Decimal("0"),
)


print()
print("THOUGHTMETRIC CHANNEL CAC AUDIT")
print("=" * 72)

print(
    "Date:",
    REPORT_DATE,
)

print()

print("META")
print("-" * 72)

print(
    "Spend:",
    f"${meta_spend:,.2f}",
)

print(
    "Attributed new customers:",
    meta_new_customers,
)

if meta_new_customers:
    print(
        "Attributed CAC:",
        f"${meta_spend / meta_new_customers:,.2f}",
    )


print()
print("EVERFLOW")
print("-" * 72)

print(
    "Payout:",
    f"${everflow_payout:,.2f}",
)

print(
    "Attributed new customers:",
    everflow_new_customers,
)

if everflow_new_customers:
    print(
        "Attributed CAC:",
        f"${everflow_payout / everflow_new_customers:,.2f}",
    )


print()
print("RAW THOUGHTMETRIC CHANNELS")
print("-" * 72)

for row in rows:
    print(
        f"{row.channel_key:<20} "
        f"orders={row.orders:<10} "
        f"new={row.new_customer_orders:<10} "
        f"sales=${row.attributed_total_sales:,.2f}"
    )