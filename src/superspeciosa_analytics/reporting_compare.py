from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from superspeciosa_analytics.reporting import (
    CommercialSummary,
    get_commercial_summary,
)
from superspeciosa_analytics.reporting_time import (
    reporting_date_range_to_utc,
)


@dataclass(frozen=True)
class MetricComparison:
    current: Decimal
    previous: Decimal
    absolute_change: Decimal
    percentage_change: Decimal | None


@dataclass(frozen=True)
class CountComparison:
    current: int
    previous: int
    absolute_change: int
    percentage_change: Decimal | None


@dataclass(frozen=True)
class CommercialComparison:
    current: CommercialSummary
    previous: CommercialSummary

    current_start: date
    current_end: date
    previous_start: date
    previous_end: date

    product_revenue: MetricComparison
    qualifying_orders: CountComparison
    average_order_value: MetricComparison

    new_customers: CountComparison
    new_customer_revenue: MetricComparison

    returning_customers: CountComparison
    returning_customer_revenue: MetricComparison

    meta_spend: MetricComparison
    manual_spend: MetricComparison
    total_marketing_spend: MetricComparison

    blended_marketing_efficiency: MetricComparison | None
    blended_new_customer_acquisition_cost: MetricComparison | None


def _percentage_change(
    current: Decimal,
    previous: Decimal,
) -> Decimal | None:
    if previous == 0:
        return None

    return (
        (current - previous)
        / previous
        * Decimal("100")
    )


def _metric_comparison(
    current: Decimal,
    previous: Decimal,
) -> MetricComparison:
    return MetricComparison(
        current=current,
        previous=previous,
        absolute_change=(
            current - previous
        ),
        percentage_change=_percentage_change(
            current,
            previous,
        ),
    )


def _count_comparison(
    current: int,
    previous: int,
) -> CountComparison:
    percentage_change = (
        _percentage_change(
            Decimal(current),
            Decimal(previous),
        )
    )

    return CountComparison(
        current=current,
        previous=previous,
        absolute_change=(
            current - previous
        ),
        percentage_change=percentage_change,
    )


def _optional_metric_comparison(
    current: Decimal | None,
    previous: Decimal | None,
) -> MetricComparison | None:
    if (
        current is None
        or previous is None
    ):
        return None

    return _metric_comparison(
        current,
        previous,
    )


def get_commercial_comparison(
    session: Session,
    *,
    start: date,
    end: date,
) -> CommercialComparison:
    """
    Compare [start, end) with the immediately
    preceding period of equal length.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    period_days = (
        end - start
    ).days

    previous_end = start

    previous_start = (
        previous_end
        - timedelta(days=period_days)
    )

    current_start_utc, current_end_utc = (
        reporting_date_range_to_utc(
            start=start,
            end=end,
        )
    )

    previous_start_utc, previous_end_utc = (
        reporting_date_range_to_utc(
            start=previous_start,
            end=previous_end,
        )
    )

    current = get_commercial_summary(
        session,
        start=current_start_utc,
        end=current_end_utc,
        report_start_date=start,
        report_end_date=end,
    )

    previous = get_commercial_summary(
        session,
        start=previous_start_utc,
        end=previous_end_utc,
        report_start_date=previous_start,
        report_end_date=previous_end,
    )

    return CommercialComparison(
        current=current,
        previous=previous,

        current_start=start,
        current_end=end,
        previous_start=previous_start,
        previous_end=previous_end,

        product_revenue=_metric_comparison(
            current.product_revenue,
            previous.product_revenue,
        ),

        qualifying_orders=_count_comparison(
            current.qualifying_orders,
            previous.qualifying_orders,
        ),

        average_order_value=_metric_comparison(
            current.average_order_value,
            previous.average_order_value,
        ),

        new_customers=_count_comparison(
            current.new_customers,
            previous.new_customers,
        ),

        new_customer_revenue=_metric_comparison(
            current.new_customer_revenue,
            previous.new_customer_revenue,
        ),

        returning_customers=_count_comparison(
            current.returning_customers,
            previous.returning_customers,
        ),

        returning_customer_revenue=_metric_comparison(
            current.returning_customer_revenue,
            previous.returning_customer_revenue,
        ),

        meta_spend=_metric_comparison(
            current.meta_spend,
            previous.meta_spend,
        ),

        manual_spend=_metric_comparison(
            current.manual_spend,
            previous.manual_spend,
        ),

        total_marketing_spend=_metric_comparison(
            current.total_marketing_spend,
            previous.total_marketing_spend,
        ),

        blended_marketing_efficiency=(
            _optional_metric_comparison(
                current.blended_marketing_efficiency,
                previous.blended_marketing_efficiency,
            )
        ),

        blended_new_customer_acquisition_cost=(
            _optional_metric_comparison(
                current.blended_new_customer_acquisition_cost,
                previous.blended_new_customer_acquisition_cost,
            )
        ),
    )