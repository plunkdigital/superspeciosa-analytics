import argparse
import time as time_module
from datetime import UTC, datetime, time
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order
from superspeciosa_analytics.shopify_ingest import (
    upsert_orders,
)
from superspeciosa_analytics.shopify_mapper import (
    map_shopify_order,
)
from superspeciosa_analytics.shopify_orders import (
    fetch_orders_by_processed_range,
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

print(
    f"Fetching Shopify orders from "
    f"{start.isoformat()} to {end.isoformat()}..."
)

payloads = fetch_orders_by_processed_range(
    start=start,
    end=end,
)

print(
    f"Fetched {len(payloads)} Shopify orders."
)

mapped_orders = [
    map_shopify_order(payload)
    for payload in payloads
]

source_ids = {
    order.shopify_order_id
    for order in mapped_orders
}

source_revenue = sum(
    (
        order.product_revenue
        for order in mapped_orders
    ),
    Decimal("0"),
)

source_shipping = sum(
    (
        order.shipping_amount
        for order in mapped_orders
    ),
    Decimal("0"),
)

source_tax = sum(
    (
        order.tax_amount
        for order in mapped_orders
    ),
    Decimal("0"),
)

BATCH_SIZE = 200

with SessionLocal() as session:
    created = 0
    total = len(mapped_orders)

    for start_index in range(
        0,
        total,
        BATCH_SIZE,
    ):
        batch = mapped_orders[
            start_index:start_index + BATCH_SIZE
        ]

        created += upsert_orders(
            session,
            batch,
        )

        session.commit()

        processed = min(
            start_index + BATCH_SIZE,
            total,
        )

        print(
            f"Imported {processed}/{total} orders "
            f"({created} new)...",
            flush=True,
        )

        # Keep memory bounded during large backfills.
        session.expunge_all()

        time_module.sleep(0.25)

    db_orders = session.scalars(
        select(Order)
        .where(Order.processed_at >= start)
        .where(Order.processed_at < end)
    ).all()

    db_ids = {
        order.shopify_order_id
        for order in db_orders
    }

    db_revenue = sum(
        (
            order.product_revenue
            for order in db_orders
        ),
        Decimal("0"),
    )

    db_shipping = sum(
        (
            order.shipping_amount
            for order in db_orders
        ),
        Decimal("0"),
    )

    db_tax = sum(
        (
            order.tax_amount
            for order in db_orders
        ),
        Decimal("0"),
    )

print()
print(f"New orders inserted: {created}")
print()

print("Reconciliation")
print("-" * 50)

print(
    f"Order count: {len(db_ids)} DB "
    f"/ {len(source_ids)} Shopify"
)

print(
    f"Revenue: {db_revenue} DB "
    f"/ {source_revenue} Shopify"
)

print(
    f"Shipping: {db_shipping} DB "
    f"/ {source_shipping} Shopify"
)

print(
    f"Tax: {db_tax} DB "
    f"/ {source_tax} Shopify"
)

failures = []

if db_ids != source_ids:
    missing = source_ids - db_ids
    unexpected = db_ids - source_ids

    failures.append(
        f"Order ID mismatch. "
        f"Missing={len(missing)}, "
        f"unexpected={len(unexpected)}"
    )

if db_revenue != source_revenue:
    failures.append("Revenue mismatch")

if db_shipping != source_shipping:
    failures.append("Shipping mismatch")

if db_tax != source_tax:
    failures.append("Tax mismatch")

if failures:
    print()
    print("RECONCILIATION FAILED")

    for failure in failures:
        print(f"- {failure}")

    raise SystemExit(1)

print()
print("Historical range reconciliation passed.")