from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")


class ShopifyMappingError(ValueError):
    pass


@dataclass(frozen=True)
class MappedLineItem:
    shopify_line_item_id: str
    shopify_product_id: str | None
    shopify_variant_id: str | None
    title: str
    quantity: int
    gross_product_amount: Decimal
    discount_amount: Decimal
    product_revenue: Decimal


@dataclass(frozen=True)
class MappedRefund:
    shopify_refund_id: str
    created_at: datetime
    currency_code: str
    product_refund_amount: Decimal
    shipping_refund_amount: Decimal
    tax_refund_amount: Decimal
    fee_refund_amount: Decimal
    unallocated_refund_amount: Decimal
    total_refund_amount: Decimal


@dataclass(frozen=True)
class MappedOrder:
    shopify_order_id: str
    shopify_order_name: str
    shopify_customer_id: str | None

    processed_at: datetime
    shopify_updated_at: datetime | None

    has_successful_payment: bool
    display_financial_status: str | None
    is_test: bool
    cancelled_at: datetime | None

    currency_code: str

    product_revenue: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    fee_amount: Decimal
    total_charged: Decimal

    lines: tuple[MappedLineItem, ...]
    refunds: tuple[MappedRefund, ...]


def _datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def _money(value: dict[str, Any] | None) -> Decimal:
    if value is None:
        return ZERO

    return Decimal(value["shopMoney"]["amount"])


def _sum_money(
    values: list[dict[str, Any]],
    field: str,
) -> Decimal:
    return sum(
        (_money(item[field]) for item in values),
        ZERO,
    )


def _has_successful_payment(
    transactions: list[dict[str, Any]],
) -> bool:
    return any(
        transaction["status"] == "SUCCESS"
        and transaction["kind"] in {"SALE", "CAPTURE"}
        for transaction in transactions
    )


def _map_line_item(
    line: dict[str, Any],
) -> MappedLineItem:
    gross = _money(line["originalTotalSet"])

    discount = sum(
        (
            _money(allocation["allocatedAmountSet"])
            for allocation in line["discountAllocations"]
        ),
        ZERO,
    )

    return MappedLineItem(
        shopify_line_item_id=line["id"],
        shopify_product_id=(
            line["product"]["id"]
            if line.get("product")
            else None
        ),
        shopify_variant_id=(
            line["variant"]["id"]
            if line.get("variant")
            else None
        ),
        title=line["title"],
        quantity=line["quantity"],
        gross_product_amount=gross,
        discount_amount=discount,
        product_revenue=gross - discount,
    )


def _map_refund(
    refund: dict[str, Any],
    currency_code: str,
) -> MappedRefund:
    refund_lines = refund["refundLineItems"]["nodes"]
    shipping_lines = refund["refundShippingLines"]["nodes"]

    product_refund = _sum_money(
        refund_lines,
        "subtotalSet",
    )

    product_tax_refund = _sum_money(
        refund_lines,
        "totalTaxSet",
    )

    shipping_refund = _sum_money(
        shipping_lines,
        "subtotalAmountSet",
    )

    shipping_tax_refund = _sum_money(
        shipping_lines,
        "taxAmountSet",
    )

    total_refund = _money(
        refund["totalRefundedSet"]
    )

    tax_refund = (
        product_tax_refund
        + shipping_tax_refund
    )

    # Additional-fee refunds are not yet present in the
    # inspected Super Speciosa data.
    fee_refund = ZERO

    # Do not derive an unallocated amount per Refund object.
    # Shopify can separate refund attribution and cash movement
    # across different Refund objects.
    unallocated = ZERO

    created_at = _datetime(refund["createdAt"])

    if created_at is None:
        raise ShopifyMappingError(
            "Refund is missing createdAt"
        )

    return MappedRefund(
        shopify_refund_id=refund["id"],
        created_at=created_at,
        currency_code=currency_code,
        product_refund_amount=product_refund,
        shipping_refund_amount=shipping_refund,
        tax_refund_amount=tax_refund,
        fee_refund_amount=fee_refund,
        unallocated_refund_amount=unallocated,
        total_refund_amount=total_refund,
    )


def map_shopify_order(
    order: dict[str, Any],
) -> MappedOrder:
    if order["taxesIncluded"]:
        raise ShopifyMappingError(
            f"Order {order['name']} has taxesIncluded=True. "
            "Revenue mapping requires explicit handling."
        )

    processed_at = _datetime(order["processedAt"])

    if processed_at is None:
        raise ShopifyMappingError(
            f"Order {order['name']} has no processedAt"
        )

    currency_code = order["currencyCode"]

    lines = tuple(
        _map_line_item(line)
        for line in order["lineItems"]["nodes"]
    )

    refunds = tuple(
        _map_refund(
            refund,
            currency_code=currency_code,
        )
        for refund in order["refunds"]
    )

    return MappedOrder(
        shopify_order_id=order["id"],
        shopify_order_name=order["name"],
        shopify_customer_id=(
            order["customer"]["id"]
            if order.get("customer")
            else None
        ),
        processed_at=processed_at,
        shopify_updated_at=_datetime(
            order.get("updatedAt")
        ),
        has_successful_payment=(
            _has_successful_payment(
                order["transactions"]
            )
        ),
        display_financial_status=(
            order.get("displayFinancialStatus")
        ),
        is_test=order["test"],
        cancelled_at=_datetime(
            order.get("cancelledAt")
        ),
        currency_code=currency_code,
        product_revenue=_money(
            order["subtotalPriceSet"]
        ),
        shipping_amount=_money(
            order["totalShippingPriceSet"]
        ),
        tax_amount=_money(
            order["totalTaxSet"]
        ),
        fee_amount=_money(
            order.get(
                "originalTotalAdditionalFeesSet"
            )
        ),
        total_charged=_money(
            order["totalPriceSet"]
        ),
        lines=lines,
        refunds=refunds,
    )