from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from superspeciosa_analytics.models import (
    Customer,
    Order,
    OrderLine,
    Refund,
)
from superspeciosa_analytics.shopify_mapper import (
    MappedOrder,
)


def upsert_orders(
    session: Session,
    mapped_orders: Sequence[MappedOrder],
) -> int:
    """
    Insert or update a batch of mapped Shopify orders.

    Existing customers and orders are fetched once per batch.

    Returns the number of newly created orders.
    """
    if not mapped_orders:
        return 0

    now = datetime.now(UTC)

    customer_ids = {
        order.shopify_customer_id
        for order in mapped_orders
        if order.shopify_customer_id is not None
    }

    if customer_ids:
        existing_customers = {
            customer.shopify_customer_id: customer
            for customer in session.scalars(
                select(Customer).where(
                    Customer.shopify_customer_id.in_(
                        customer_ids
                    )
                )
            ).all()
        }
    else:
        existing_customers = {}

    order_ids = {
        order.shopify_order_id
        for order in mapped_orders
    }

    existing_orders = {
        order.shopify_order_id: order
        for order in session.scalars(
            select(Order)
            .where(
                Order.shopify_order_id.in_(
                    order_ids
                )
            )
            .options(
                selectinload(Order.lines),
                selectinload(Order.refunds),
            )
        ).all()
    }

    created = 0

    for mapped in mapped_orders:
        customer = None

        if mapped.shopify_customer_id is not None:
            customer = existing_customers.get(
                mapped.shopify_customer_id
            )

            if customer is None:
                customer = Customer(
                    shopify_customer_id=(
                        mapped.shopify_customer_id
                    ),
                    shopify_created_at=None,
                    shopify_updated_at=None,
                    ingested_at=now,
                )

                session.add(customer)

                existing_customers[
                    mapped.shopify_customer_id
                ] = customer
            else:
                customer.ingested_at = now

        order = existing_orders.get(
            mapped.shopify_order_id
        )

        if order is None:
            order = Order(
                shopify_order_id=(
                    mapped.shopify_order_id
                ),
                shopify_order_name=(
                    mapped.shopify_order_name
                ),
                processed_at=mapped.processed_at,
                has_successful_payment=(
                    mapped.has_successful_payment
                ),
                display_financial_status=(
                    mapped.display_financial_status
                ),
                is_test=mapped.is_test,
                cancelled_at=mapped.cancelled_at,
                currency_code=mapped.currency_code,
                product_revenue=(
                    mapped.product_revenue
                ),
                shipping_amount=(
                    mapped.shipping_amount
                ),
                tax_amount=mapped.tax_amount,
                fee_amount=mapped.fee_amount,
                total_charged=(
                    mapped.total_charged
                ),
                shopify_updated_at=(
                    mapped.shopify_updated_at
                ),
                ingested_at=now,
            )

            session.add(order)

            existing_orders[
                mapped.shopify_order_id
            ] = order

            created += 1

        order.customer = customer
        order.shopify_order_name = (
            mapped.shopify_order_name
        )
        order.processed_at = mapped.processed_at
        order.has_successful_payment = (
            mapped.has_successful_payment
        )
        order.display_financial_status = (
            mapped.display_financial_status
        )
        order.is_test = mapped.is_test
        order.cancelled_at = mapped.cancelled_at
        order.currency_code = mapped.currency_code
        order.product_revenue = (
            mapped.product_revenue
        )
        order.shipping_amount = (
            mapped.shipping_amount
        )
        order.tax_amount = mapped.tax_amount
        order.fee_amount = mapped.fee_amount
        order.total_charged = (
            mapped.total_charged
        )
        order.shopify_updated_at = (
            mapped.shopify_updated_at
        )
        order.ingested_at = now

        existing_lines = {
            line.shopify_line_item_id: line
            for line in order.lines
        }

        incoming_line_ids = {
            line.shopify_line_item_id
            for line in mapped.lines
        }

        for mapped_line in mapped.lines:
            line = existing_lines.get(
                mapped_line.shopify_line_item_id
            )

            if line is None:
                line = OrderLine(
                    shopify_line_item_id=(
                        mapped_line.shopify_line_item_id
                    ),
                )

                order.lines.append(line)

            line.shopify_product_id = (
                mapped_line.shopify_product_id
            )
            line.shopify_variant_id = (
                mapped_line.shopify_variant_id
            )
            line.title = mapped_line.title
            line.quantity = mapped_line.quantity
            line.gross_product_amount = (
                mapped_line.gross_product_amount
            )
            line.discount_amount = (
                mapped_line.discount_amount
            )
            line.product_revenue = (
                mapped_line.product_revenue
            )

        for external_id, line in existing_lines.items():
            if external_id not in incoming_line_ids:
                session.delete(line)

        existing_refunds = {
            refund.shopify_refund_id: refund
            for refund in order.refunds
        }

        incoming_refund_ids = {
            refund.shopify_refund_id
            for refund in mapped.refunds
        }

        for mapped_refund in mapped.refunds:
            refund = existing_refunds.get(
                mapped_refund.shopify_refund_id
            )

            if refund is None:
                refund = Refund(
                    shopify_refund_id=(
                        mapped_refund.shopify_refund_id
                    ),
                )

                order.refunds.append(refund)

            refund.created_at = (
                mapped_refund.created_at
            )
            refund.currency_code = (
                mapped_refund.currency_code
            )
            refund.product_refund_amount = (
                mapped_refund.product_refund_amount
            )
            refund.shipping_refund_amount = (
                mapped_refund.shipping_refund_amount
            )
            refund.tax_refund_amount = (
                mapped_refund.tax_refund_amount
            )
            refund.fee_refund_amount = (
                mapped_refund.fee_refund_amount
            )
            refund.unallocated_refund_amount = (
                mapped_refund.unallocated_refund_amount
            )
            refund.total_refund_amount = (
                mapped_refund.total_refund_amount
            )
            refund.ingested_at = now

        for external_id, refund in existing_refunds.items():
            if external_id not in incoming_refund_ids:
                session.delete(refund)

    return created


def upsert_order(
    session: Session,
    mapped: MappedOrder,
) -> bool:
    """
    Compatibility wrapper for single-order imports.
    """
    return upsert_orders(
        session,
        [mapped],
    ) == 1