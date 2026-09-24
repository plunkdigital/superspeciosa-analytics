from datetime import UTC, datetime
from decimal import Decimal

import pytest

from superspeciosa_analytics.order_rules import (
    OrderClassification,
    OrderFacts,
    classify_customer_orders,
    is_qualifying_order,
    remaining_revenue,
)


def make_order(
    order_id: str = "1",
    customer_key: str | None = "customer-1",
    revenue: str = "100.00",
    refund: str = "0.00",
    paid: bool = True,
    test: bool = False,
    cancelled: bool = False,
    day: int = 1,
) -> OrderFacts:
    return OrderFacts(
        order_id=order_id,
        processed_at=datetime(2026, 1, day, tzinfo=UTC),
        customer_key=customer_key,
        has_successful_payment=paid,
        is_test=test,
        is_cancelled=cancelled,
        product_revenue=Decimal(revenue),
        product_refund_amount=Decimal(refund),
    )


def test_paid_positive_order_qualifies():
    assert is_qualifying_order(make_order())


def test_zero_value_order_does_not_qualify():
    assert not is_qualifying_order(
        make_order(revenue="0.00")
    )


@pytest.mark.parametrize(
    ("paid", "test", "cancelled"),
    [
        (False, False, False),
        (True, True, False),
        (True, False, True),
    ],
)
def test_invalid_order_states_do_not_qualify(
    paid,
    test,
    cancelled,
):
    assert not is_qualifying_order(
        make_order(
            paid=paid,
            test=test,
            cancelled=cancelled,
        )
    )


def test_refund_does_not_remove_qualifying_order():
    order = make_order(
        revenue="100.00",
        refund="100.00",
    )

    assert is_qualifying_order(order)
    assert remaining_revenue(order) == Decimal("0.00")


def test_zero_value_order_does_not_create_customer_history():
    orders = [
        make_order(
            order_id="zero",
            revenue="0.00",
            day=1,
        ),
        make_order(
            order_id="first-real-order",
            revenue="50.00",
            day=2,
        ),
    ]

    result = classify_customer_orders(orders)

    assert (
        result["zero"]
        == OrderClassification.NOT_QUALIFYING
    )
    assert (
        result["first-real-order"]
        == OrderClassification.NEW
    )


def test_second_qualifying_order_is_returning():
    orders = [
        make_order(
            order_id="first",
            day=1,
        ),
        make_order(
            order_id="second",
            day=2,
        ),
    ]

    result = classify_customer_orders(orders)

    assert result["first"] == OrderClassification.NEW
    assert result["second"] == OrderClassification.RETURNING


def test_full_refund_does_not_reset_customer_history():
    orders = [
        make_order(
            order_id="first",
            revenue="100.00",
            refund="100.00",
            day=1,
        ),
        make_order(
            order_id="second",
            revenue="40.00",
            day=2,
        ),
    ]

    result = classify_customer_orders(orders)

    assert result["first"] == OrderClassification.NEW
    assert result["second"] == OrderClassification.RETURNING


def test_customer_without_identity_is_unclassified():
    order = make_order(
        customer_key=None,
    )

    result = classify_customer_orders([order])

    assert result["1"] == OrderClassification.UNCLASSIFIED