from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Iterable


ZERO = Decimal("0")


class OrderClassification(StrEnum):
    NEW = "new"
    RETURNING = "returning"
    UNCLASSIFIED = "unclassified"
    NOT_QUALIFYING = "not_qualifying"


@dataclass(frozen=True)
class OrderFacts:
    order_id: str
    processed_at: datetime
    customer_key: str | None

    has_successful_payment: bool
    is_test: bool
    is_cancelled: bool

    product_revenue: Decimal
    product_refund_amount: Decimal = ZERO


def is_qualifying_order(order: OrderFacts) -> bool:
    """
    A qualifying Super Speciosa order:

    - has had a successful payment
    - is not a test order
    - is not cancelled
    - has product revenue greater than $0

    product_revenue excludes shipping, tax and fees.

    Refunds do not change whether the original order qualified.
    """
    return (
        order.has_successful_payment
        and not order.is_test
        and not order.is_cancelled
        and order.product_revenue > ZERO
    )


def remaining_revenue(order: OrderFacts) -> Decimal:
    """
    Product revenue remaining after product refunds.

    Shipping, tax and fee refunds are intentionally excluded from this
    calculation because they are not Super Speciosa revenue.
    """
    return order.product_revenue - order.product_refund_amount


def classify_customer_orders(
    orders: Iterable[OrderFacts],
) -> dict[str, OrderClassification]:
    """
    Classify qualifying orders as new or returning.

    Non-qualifying orders never establish customer history.

    Orders without a usable customer identity remain unclassified until
    the Shopify guest-customer fallback rule is defined.
    """
    ordered = sorted(
        orders,
        key=lambda order: (order.processed_at, order.order_id),
    )

    seen_customers: set[str] = set()
    classifications: dict[str, OrderClassification] = {}

    for order in ordered:
        if not is_qualifying_order(order):
            classifications[order.order_id] = (
                OrderClassification.NOT_QUALIFYING
            )
            continue

        if order.customer_key is None:
            classifications[order.order_id] = (
                OrderClassification.UNCLASSIFIED
            )
            continue

        if order.customer_key in seen_customers:
            classifications[order.order_id] = (
                OrderClassification.RETURNING
            )
        else:
            classifications[order.order_id] = OrderClassification.NEW
            seen_customers.add(order.customer_key)

    return classifications