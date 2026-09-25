from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order
from superspeciosa_analytics.shopify_mapper import (
    map_shopify_order,
)
from superspeciosa_analytics.shopify_orders import (
    fetch_orders_by_processed_range,
)


START = datetime(
    2022,
    9,
    1,
    tzinfo=UTC,
)

END = datetime(
    2022,
    10,
    1,
    tzinfo=UTC,
)


payloads = fetch_orders_by_processed_range(
    start=START,
    end=END,
)

mapped_orders = [
    map_shopify_order(payload)
    for payload in payloads
]

source_by_id = {
    order.shopify_order_id: order
    for order in mapped_orders
}

source_ids = set(source_by_id)


with SessionLocal() as session:
    db_orders = session.scalars(
        select(Order)
        .where(Order.processed_at >= START)
        .where(Order.processed_at < END)
    ).all()

    db_ids = {
        order.shopify_order_id
        for order in db_orders
    }

    missing_ids = source_ids - db_ids
    unexpected_ids = db_ids - source_ids

    print(
        f"Shopify IDs: {len(source_ids)}"
    )

    print(
        f"DB IDs in range: {len(db_ids)}"
    )

    print(
        f"Missing: {len(missing_ids)}"
    )

    print(
        f"Unexpected: {len(unexpected_ids)}"
    )

    print()

    for shopify_id in sorted(missing_ids):
        source_order = source_by_id[
            shopify_id
        ]

        print("=" * 70)
        print("MISSING ORDER")
        print("=" * 70)

        print(
            "Shopify ID:",
            source_order.shopify_order_id,
        )

        print(
            "Order:",
            source_order.shopify_order_name,
        )

        print(
            "Processed:",
            source_order.processed_at,
        )

        print(
            "Shopify created:",
            source_order.shopify_created_at,
        )

        print(
            "Reporting date:",
            source_order.reporting_order_at,
        )

        print(
            "Source name:",
            source_order.source_name,
        )

        print(
            "Source system:",
            source_order.source_system,
        )

        print(
            "Source order ID:",
            source_order.source_order_id,
        )

        print(
            "Woo customer ID:",
            source_order.woo_customer_id,
        )

        print(
            "Successful payment:",
            source_order.has_successful_payment,
        )

        print(
            "Financial status:",
            source_order.display_financial_status,
        )

        print(
            "Test:",
            source_order.is_test,
        )

        print(
            "Cancelled:",
            source_order.cancelled_at is not None,
        )

        print(
            "Revenue:",
            source_order.product_revenue,
        )

        print(
            "Shipping:",
            source_order.shipping_amount,
        )

        print(
            "Tax:",
            source_order.tax_amount,
        )

        print(
            "Total charged:",
            source_order.total_charged,
        )

        print(
            "Line count:",
            len(source_order.lines),
        )

        print(
            "Refund count:",
            len(source_order.refunds),
        )

        print()

        existing = session.scalar(
            select(Order).where(
                Order.shopify_order_id
                == shopify_id
            )
        )

        if existing is None:
            print(
                "DB lookup by Shopify ID: "
                "NOT FOUND ANYWHERE"
            )

        else:
            print(
                "DB lookup by Shopify ID: "
                "FOUND OUTSIDE RANGE"
            )

            print(
                "DB processed_at:",
                existing.processed_at,
            )

            print(
                "DB reporting_order_at:",
                existing.reporting_order_at,
            )

            print(
                "DB source:",
                existing.source_name,
                "/",
                existing.source_system,
            )

            print(
                "DB revenue:",
                existing.product_revenue,
            )

            print(
                "DB shipping:",
                existing.shipping_amount,
            )

            print(
                "DB tax:",
                existing.tax_amount,
            )

        print()


    if unexpected_ids:
        print()
        print("=" * 70)
        print("UNEXPECTED DB ORDERS")
        print("=" * 70)

        for shopify_id in sorted(
            unexpected_ids
        ):
            order = session.scalar(
                select(Order).where(
                    Order.shopify_order_id
                    == shopify_id
                )
            )

            print(
                order.shopify_order_name,
                order.shopify_order_id,
                order.processed_at,
                order.product_revenue,
            )