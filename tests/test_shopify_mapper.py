import json
from decimal import Decimal
from pathlib import Path

import pytest

from superspeciosa_analytics.shopify_mapper import (
    ShopifyMappingError,
    map_shopify_order,
)


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    path = FIXTURES / name

    with path.open() as file:
        return json.load(file)


def test_maps_paid_order():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    order = map_shopify_order(payload)

    assert order.shopify_order_name == "TEST-1001"
    assert order.currency_code == "USD"
    assert order.has_successful_payment is True
    assert order.product_revenue == Decimal("90.00")
    assert order.shipping_amount == Decimal("5.00")
    assert order.tax_amount == Decimal("7.00")
    assert order.fee_amount == Decimal("0")
    assert order.total_charged == Decimal("102.00")


def test_maps_customer_id():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    order = map_shopify_order(payload)

    assert (
        order.shopify_customer_id
        == "gid://shopify/Customer/5001"
    )


def test_maps_line_item_discount():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    order = map_shopify_order(payload)

    line = order.lines[0]

    assert (
        line.gross_product_amount
        == Decimal("100.00")
    )

    assert (
        line.discount_amount
        == Decimal("10.00")
    )

    assert (
        line.product_revenue
        == Decimal("90.00")
    )


def test_maps_full_refund_components():
    payload = load_fixture(
        "shopify_refunded_order.json"
    )

    order = map_shopify_order(payload)

    refund = order.refunds[0]

    assert (
        refund.product_refund_amount
        == Decimal("89.00")
    )

    assert (
        refund.shipping_refund_amount
        == Decimal("9.78")
    )

    assert (
        refund.tax_refund_amount
        == Decimal("8.68")
    )

    assert (
        refund.total_refund_amount
        == Decimal("107.46")
    )

    assert (
        refund.unallocated_refund_amount
        == Decimal("0")
    )


def test_refund_does_not_change_original_revenue():
    payload = load_fixture(
        "shopify_refunded_order.json"
    )

    order = map_shopify_order(payload)

    assert (
        order.product_revenue
        == Decimal("89.00")
    )


def test_authorization_only_is_not_successful_payment():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    payload["transactions"][0]["kind"] = (
        "AUTHORIZATION"
    )

    order = map_shopify_order(payload)

    assert order.has_successful_payment is False


def test_tax_inclusive_order_is_rejected():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    payload["taxesIncluded"] = True

    with pytest.raises(
        ShopifyMappingError,
        match="taxesIncluded=True",
    ):
        map_shopify_order(payload)


def test_order_without_customer_is_supported():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    payload["customer"] = None

    order = map_shopify_order(payload)

    assert order.shopify_customer_id is None

def test_rejects_truncated_line_items():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    payload["lineItems"]["pageInfo"] = {
        "hasNextPage": True,
    }

    with pytest.raises(
        ShopifyMappingError,
        match="per-order query limit",
    ):
        map_shopify_order(payload)

def test_normalizes_decimal_woo_ids():
    payload = load_fixture(
        "shopify_paid_order.json"
    )

    payload["sourceName"] = "Matrixify App"

    payload["wooOrderId"] = {
        "value": "19907.0",
    }

    payload["wooCustomerId"] = {
        "value": "17.0",
    }

    payload["customer"]["wooCustomerId"] = {
        "value": "17.0",
    }

    order = map_shopify_order(payload)

    assert order.source_system == "woocommerce"
    assert order.source_order_id == "19907"
    assert order.woo_customer_id == "17"
    assert order.shopify_customer_woo_id == "17"