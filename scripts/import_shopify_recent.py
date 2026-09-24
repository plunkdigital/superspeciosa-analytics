from sqlalchemy import func, select

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.models import (
    Customer,
    Order,
    OrderLine,
    Refund,
)
from superspeciosa_analytics.shopify_ingest import (
    upsert_order,
)
from superspeciosa_analytics.shopify_mapper import (
    map_shopify_order,
)
from superspeciosa_analytics.shopify_orders import (
    fetch_recent_orders,
)


def counts(session):
    return {
        "customers": session.scalar(
            select(func.count()).select_from(Customer)
        ),
        "orders": session.scalar(
            select(func.count()).select_from(Order)
        ),
        "order_lines": session.scalar(
            select(func.count()).select_from(OrderLine)
        ),
        "refunds": session.scalar(
            select(func.count()).select_from(Refund)
        ),
    }


payloads = fetch_recent_orders(limit=10)

mapped_orders = [
    map_shopify_order(payload)
    for payload in payloads
]

print(f"Fetched {len(mapped_orders)} Shopify orders.")

with SessionLocal() as session:
    print("Before:", counts(session))

    created_first = sum(
        upsert_order(session, order)
        for order in mapped_orders
    )

    session.commit()

    first_counts = counts(session)

    print(
        f"First pass: {created_first} new orders"
    )
    print("After first pass:", first_counts)

    created_second = sum(
        upsert_order(session, order)
        for order in mapped_orders
    )

    session.commit()

    second_counts = counts(session)

    print(
        f"Second pass: {created_second} new orders"
    )
    print("After second pass:", second_counts)

    if first_counts != second_counts:
        raise RuntimeError(
            "Idempotency check failed: row counts changed "
            "when importing the same Shopify payload twice."
        )

    if created_second != 0:
        raise RuntimeError(
            "Idempotency check failed: second pass "
            "created new orders."
        )

print()
print("Idempotency check passed.")