from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from superspeciosa_analytics.models import Refund


ZERO = Decimal("0")


@dataclass(frozen=True)
class CommercialSummary:
    start: datetime
    end: datetime

    qualifying_orders: int
    product_revenue: Decimal
    average_order_value: Decimal

    new_customers: int
    new_customer_orders: int
    new_customer_revenue: Decimal

    returning_customers: int
    returning_customer_orders: int
    returning_customer_revenue: Decimal

    unresolved_orders: int
    unresolved_revenue: Decimal

    refund_events: int
    total_cash_refunded: Decimal
    product_refund_amount: Decimal
    shipping_refund_amount: Decimal
    tax_refund_amount: Decimal


CUSTOMER_QUERY = text(
    """
    SELECT
        COUNT(*) AS qualifying_orders,

        COALESCE(
            SUM(product_revenue),
            0
        ) AS product_revenue,

        COUNT(*) FILTER (
            WHERE customer_classification = 'new'
        ) AS new_customer_orders,

        COUNT(
            DISTINCT customer_identity
        ) FILTER (
            WHERE customer_classification = 'new'
        ) AS new_customers,

        COALESCE(
            SUM(product_revenue) FILTER (
                WHERE customer_classification = 'new'
            ),
            0
        ) AS new_customer_revenue,

        COUNT(*) FILTER (
            WHERE customer_classification = 'returning'
        ) AS returning_customer_orders,

        COUNT(
            DISTINCT customer_identity
        ) FILTER (
            WHERE customer_classification = 'returning'
        ) AS returning_customers,

        COALESCE(
            SUM(product_revenue) FILTER (
                WHERE customer_classification = 'returning'
            ),
            0
        ) AS returning_customer_revenue,

        COUNT(*) FILTER (
            WHERE customer_classification = 'unresolved'
        ) AS unresolved_orders,

        COALESCE(
            SUM(product_revenue) FILTER (
                WHERE customer_classification = 'unresolved'
            ),
            0
        ) AS unresolved_revenue

    FROM reporting_order_classification

    WHERE
        reporting_order_at >= :start
        AND reporting_order_at < :end
    """
)


def get_commercial_summary(
    session: Session,
    *,
    start: datetime,
    end: datetime,
) -> CommercialSummary:
    if start >= end:
        raise ValueError(
            "Start datetime must be before end datetime."
        )

    customer = session.execute(
        CUSTOMER_QUERY,
        {
            "start": start,
            "end": end,
        },
    ).mappings().one()

    refund = session.execute(
        select(
            func.count(Refund.id),
            func.coalesce(
                func.sum(
                    Refund.total_refund_amount
                ),
                ZERO,
            ),
            func.coalesce(
                func.sum(
                    Refund.product_refund_amount
                ),
                ZERO,
            ),
            func.coalesce(
                func.sum(
                    Refund.shipping_refund_amount
                ),
                ZERO,
            ),
            func.coalesce(
                func.sum(
                    Refund.tax_refund_amount
                ),
                ZERO,
            ),
        )
        .where(
            Refund.created_at >= start
        )
        .where(
            Refund.created_at < end
        )
    ).one()

    qualifying_orders = int(
        customer["qualifying_orders"]
    )

    product_revenue = Decimal(
        customer["product_revenue"]
    )

    if qualifying_orders:
        average_order_value = (
            product_revenue
            / qualifying_orders
        )
    else:
        average_order_value = ZERO

    return CommercialSummary(
        start=start,
        end=end,

        qualifying_orders=qualifying_orders,
        product_revenue=product_revenue,
        average_order_value=average_order_value,

        new_customers=int(
            customer["new_customers"]
        ),
        new_customer_orders=int(
            customer["new_customer_orders"]
        ),
        new_customer_revenue=Decimal(
            customer["new_customer_revenue"]
        ),

        returning_customers=int(
            customer["returning_customers"]
        ),
        returning_customer_orders=int(
            customer["returning_customer_orders"]
        ),
        returning_customer_revenue=Decimal(
            customer[
                "returning_customer_revenue"
            ]
        ),

        unresolved_orders=int(
            customer["unresolved_orders"]
        ),
        unresolved_revenue=Decimal(
            customer["unresolved_revenue"]
        ),

        refund_events=int(refund[0]),
        total_cash_refunded=Decimal(
            refund[1]
        ),
        product_refund_amount=Decimal(
            refund[2]
        ),
        shipping_refund_amount=Decimal(
            refund[3]
        ),
        tax_refund_amount=Decimal(
            refund[4]
        ),
    )