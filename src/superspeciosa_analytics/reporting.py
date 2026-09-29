from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
    ManualSpend,
    MetaDailySpend,
    Refund,
)


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

    meta_spend: Decimal
    manual_spend: Decimal
    everflow_payout: Decimal
    total_marketing_spend: Decimal

    blended_marketing_efficiency: Decimal | None
    blended_new_customer_acquisition_cost: Decimal | None


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

def _manual_spend_for_period(
    session: Session,
    *,
    start: date,
    end: date,
) -> Decimal:
    """
    Straight-line recognition across inclusive service dates.

    Report period is [start, end).
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    rows = session.scalars(
        select(ManualSpend)
        .where(
            ManualSpend.status == "delivered"
        )
        .where(
            ManualSpend.service_start_date < end
        )
        .where(
            ManualSpend.service_end_date >= start
        )
    ).all()

    total = ZERO

    for row in rows:
        service_days = (
            row.service_end_date
            - row.service_start_date
        ).days + 1

        overlap_start = max(
            start,
            row.service_start_date,
        )

        overlap_end = min(
            end,
            row.service_end_date
            + timedelta(days=1),
        )

        overlap_days = (
            overlap_end - overlap_start
        ).days

        if overlap_days <= 0:
            continue

        daily_amount = (
            row.amount
            / Decimal(service_days)
        )

        total += (
            daily_amount
            * Decimal(overlap_days)
        )

    return total

def get_commercial_summary(
    session: Session,
    *,
    start: datetime,
    end: datetime,
    report_start_date: date,
    report_end_date: date,
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

    refund = session.execute(
        select(
            func.count(Refund.id).filter(
                Refund.total_refund_amount > ZERO
            ),
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

    meta_spend = session.scalar(
        select(
            func.coalesce(
                func.sum(
                    MetaDailySpend.spend
                ),
                ZERO,
            )
        )
        .where(
            MetaDailySpend.report_date
            >= report_start_date
        )
        .where(
            MetaDailySpend.report_date
            < report_end_date
        )
    )

    meta_spend = Decimal(
        meta_spend
    )

    everflow_payout = session.scalar(
        select(
            func.sum(
                EverflowDailyPerformance.payout
            )
        )
        .where(
            EverflowDailyPerformance.report_date
            >= report_start_date
        )
        .where(
            EverflowDailyPerformance.report_date
            < report_end_date
        )
    ) or ZERO

    manual_spend = (
        _manual_spend_for_period(
            session,
            start=report_start_date,
            end=report_end_date,
        )
    )

    total_marketing_spend = (
        meta_spend
        + everflow_payout
        + manual_spend
    )

    if total_marketing_spend > ZERO:
        blended_marketing_efficiency = (
            product_revenue
            / total_marketing_spend
        )

        if int(
            customer["new_customers"]
        ) > 0:
            blended_new_customer_acquisition_cost = (
                total_marketing_spend
                / int(
                    customer["new_customers"]
                )
            )
        else:
            blended_new_customer_acquisition_cost = None
    else:
        blended_marketing_efficiency = None
        blended_new_customer_acquisition_cost = None

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
        meta_spend=meta_spend,
        manual_spend=manual_spend,
        everflow_payout=everflow_payout,
        total_marketing_spend=(
            total_marketing_spend
        ),
        blended_marketing_efficiency=(
            blended_marketing_efficiency
        ),
        blended_new_customer_acquisition_cost=(
            blended_new_customer_acquisition_cost
        ),
    )