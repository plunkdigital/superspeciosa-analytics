import csv
from pathlib import Path

from sqlalchemy import select

from superspeciosa_analytics.customer_identity import (
    CustomerIdentityMethod,
    resolve_customer_identity,
)
from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Customer, Order


OUTPUT = Path(
    "data/exports/unresolved_orders.csv"
)


def unresolved_reason(
    order: Order,
    customer: Customer | None,
) -> str:
    if (
        order.source_system == "woocommerce"
        and order.woo_customer_id == "0"
        and customer is None
    ):
        return "woocommerce_guest_without_customer_link"

    if (
        order.source_system == "woocommerce"
        and order.woo_customer_id == "0"
    ):
        return "woocommerce_guest_without_resolvable_identity"

    if (
        order.source_system == "shopify"
        and customer is None
    ):
        return "shopify_order_without_customer"

    if (
        order.source_system == "matrixify_unknown"
    ):
        return "matrixify_order_without_resolvable_identity"

    return "no_resolvable_customer_identity"


with SessionLocal() as session:
    rows = session.execute(
        select(
            Order,
            Customer,
        )
        .outerjoin(
            Customer,
            Order.customer_id == Customer.id,
        )
        .where(
            Order.has_successful_payment.is_(True)
        )
        .where(
            Order.is_test.is_(False)
        )
        .where(
            Order.cancelled_at.is_(None)
        )
        .where(
            Order.product_revenue > 0
        )
        .where(
            Order.reporting_order_at.is_not(None)
        )
        .order_by(
            Order.reporting_order_at,
            Order.id,
        )
    )

    unresolved = []

    for order, customer in rows:
        identity_key, method = (
            resolve_customer_identity(
                source_system=order.source_system,
                order_woo_customer_id=(
                    order.woo_customer_id
                ),
                shopify_customer_id=(
                    customer.shopify_customer_id
                    if customer
                    else None
                ),
                customer_woo_customer_id=(
                    customer.woo_customer_id
                    if customer
                    else None
                ),
            )
        )

        if (
            method
            != CustomerIdentityMethod.UNRESOLVED
        ):
            continue

        unresolved.append(
            {
                "shopify_order_name": (
                    order.shopify_order_name
                ),
                "shopify_order_id": (
                    order.shopify_order_id
                ),
                "reporting_order_at": (
                    order.reporting_order_at.isoformat()
                ),
                "source_system": (
                    order.source_system
                ),
                "source_name": (
                    order.source_name
                ),
                "source_order_id": (
                    order.source_order_id
                ),
                "order_woo_customer_id": (
                    order.woo_customer_id
                ),
                "shopify_customer_id": (
                    customer.shopify_customer_id
                    if customer
                    else None
                ),
                "customer_woo_customer_id": (
                    customer.woo_customer_id
                    if customer
                    else None
                ),
                "product_revenue": (
                    order.product_revenue
                ),
                "shipping_amount": (
                    order.shipping_amount
                ),
                "tax_amount": (
                    order.tax_amount
                ),
                "total_charged": (
                    order.total_charged
                ),
                "financial_status": (
                    order.display_financial_status
                ),
                "reason": unresolved_reason(
                    order,
                    customer,
                ),
                "review_status": "",
                "resolved_customer_reference": "",
                "review_notes": "",
            }
        )


fieldnames = [
    "shopify_order_name",
    "shopify_order_id",
    "reporting_order_at",
    "source_system",
    "source_name",
    "source_order_id",
    "order_woo_customer_id",
    "shopify_customer_id",
    "customer_woo_customer_id",
    "product_revenue",
    "shipping_amount",
    "tax_amount",
    "total_charged",
    "financial_status",
    "reason",
    "review_status",
    "resolved_customer_reference",
    "review_notes",
]


with OUTPUT.open(
    "w",
    newline="",
    encoding="utf-8",
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(unresolved)


print(
    f"Exported {len(unresolved)} "
    f"unresolved qualifying orders."
)

print(
    f"Output: {OUTPUT}"
)