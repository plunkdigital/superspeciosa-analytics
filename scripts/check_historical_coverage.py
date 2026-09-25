from sqlalchemy import func, select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order


with SessionLocal() as session:
    first_order = session.scalar(
        select(func.min(Order.reporting_order_at))
    )

    last_order = session.scalar(
        select(func.max(Order.reporting_order_at))
    )

    order_count = session.scalar(
        select(func.count()).select_from(Order)
    )

    source_counts = session.execute(
        select(
            Order.source_system,
            func.count(),
        )
        .group_by(Order.source_system)
        .order_by(Order.source_system)
    ).all()

print("Historical coverage")
print("-" * 50)

print("First order:", first_order)
print("Last order:", last_order)
print("Total orders:", order_count)

print()
print("Source systems:")

for source_system, count in source_counts:
    print(
        f"  {source_system!r}: {count}"
    )