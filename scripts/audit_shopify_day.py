from datetime import date

from sqlalchemy import func, select, text

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order
from superspeciosa_analytics.reporting_time import (
    reporting_date_range_to_utc,
)


report_date = date(2026, 9, 1)
next_date = date(2026, 9, 30)

start, end = reporting_date_range_to_utc(
    start=report_date,
    end=next_date,
)


with SessionLocal() as session:
    raw_count = session.scalar(
        select(
            func.count(Order.id)
        )
        .where(
            Order.reporting_order_at >= start
        )
        .where(
            Order.reporting_order_at < end
        )
    )

    qualifying_count = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM reporting_order_classification
            WHERE reporting_order_at >= :start
              AND reporting_order_at < :end
            """
        ),
        {
            "start": start,
            "end": end,
        },
    ).scalar_one()

    excluded = session.execute(
        text(
            """
            SELECT o.*
            FROM orders o
            LEFT JOIN reporting_order_classification r
                ON r.order_id = o.id
            WHERE o.reporting_order_at >= :start
              AND o.reporting_order_at < :end
              AND r.order_id IS NULL
            ORDER BY o.reporting_order_at
            """
        ),
        {
            "start": start,
            "end": end,
        },
    ).mappings().all()


print()
print("SEP MTD ORDER AUDIT")
print("=" * 70)

print(
    "Raw database orders:",
    raw_count,
)

print(
    "Qualifying orders:",
    qualifying_count,
)

print(
    "Excluded orders:",
    len(excluded),
)

print()

for row in excluded:
    print("-" * 70)

    for key, value in row.items():
        if value is not None:
            print(
                f"{key}: {value}"
            )