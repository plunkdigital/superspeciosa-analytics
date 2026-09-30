from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from superspeciosa_analytics.thoughtmetric import (
    get_channel_performance,
)


ZERO = Decimal("0")


@dataclass(frozen=True)
class ThoughtMetricDailyChannelRecord:
    report_date: date
    channel_key: str
    orders: Decimal
    new_customer_orders: Decimal
    new_customer_sales: Decimal
    attributed_total_sales: Decimal
    converted_spend: Decimal


def _decimal(value) -> Decimal:
    if value is None:
        return ZERO

    return Decimal(
        str(value)
    )


def _record_from_row(
    *,
    report_date: date,
    row: dict,
) -> ThoughtMetricDailyChannelRecord:
    return ThoughtMetricDailyChannelRecord(
        report_date=report_date,
        channel_key=str(
            row.get(
                "channel",
                "unknown",
            )
        ),
        orders=_decimal(
            row.get(
                "orders"
            )
        ),
        new_customer_orders=_decimal(
            row.get(
                "new_customer_orders"
            )
        ),
        new_customer_sales=_decimal(
            row.get(
                "new_customer_total_sales"
            )
        ),
        attributed_total_sales=_decimal(
            row.get(
                "total_sales"
            )
        ),
        converted_spend=_decimal(
            row.get(
                "converted_spend"
            )
        ),
    )


def fetch_daily_channel_performance(
    *,
    start: date,
    end: date,
) -> tuple[
    list[ThoughtMetricDailyChannelRecord],
    list[date],
]:
    """
    Fetch ThoughtMetric data for [start, end).

    Each business day is requested separately so
    persisted rows always represent one exact day.

    No attribution-model parameter is supplied.
    ThoughtMetric therefore uses the project's
    configured attribution model.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    records = []
    checked_dates = []

    current = start

    while current < end:
        data = get_channel_performance(
            start=current,
            end=current,
        )

        rows = data.get(
            "total",
            [],
        )

        for row in rows:
            records.append(
                _record_from_row(
                    report_date=current,
                    row=row,
                )
            )

        checked_dates.append(
            current
        )

        current += timedelta(
            days=1
        )

    return records, checked_dates