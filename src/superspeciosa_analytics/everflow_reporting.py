from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from superspeciosa_analytics.everflow import (
    EverflowConfigurationError,
    get_currency,
    get_timezone_id,
    post,
)


ZERO = Decimal("0")


@dataclass(frozen=True)
class EverflowDailyPerformanceRecord:
    report_date: date
    currency_code: str
    payout: Decimal
    revenue: Decimal
    gross_sales: Decimal
    conversions: int
    clicks: int
    source_rows: int


def _decimal(value) -> Decimal:
    if value is None:
        return ZERO

    return Decimal(
        str(value)
    )


def fetch_daily_performance(
    *,
    start: date,
    end: date,
) -> list[EverflowDailyPerformanceRecord]:
    """
    Fetch Everflow daily totals for [start, end).

    One aggregate record is returned for every date,
    including dates with zero Everflow activity.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    timezone_id = get_timezone_id()

    if timezone_id is None:
        raise EverflowConfigurationError(
            "EVERFLOW_TIMEZONE_ID is not configured."
        )

    currency = get_currency()

    records = []

    current = start

    while current < end:
        response = post(
            "/networks/reporting/entity/table",
            {
                "from": current.isoformat(),
                "to": current.isoformat(),
                "timezone_id": timezone_id,
                "currency_id": currency,
                "columns": [
                    {
                        "column": "affiliate",
                    }
                ],
                "query": {
                    "filters": [],
                    "exclusions": [],
                },
            },
        )

        rows = response.get(
            "table",
            [],
        )

        payout = ZERO
        revenue = ZERO
        gross_sales = ZERO
        conversions = 0
        clicks = 0

        for row in rows:
            reporting = row.get(
                "reporting",
                {},
            )

            payout += _decimal(
                reporting.get(
                    "payout"
                )
            )

            revenue += _decimal(
                reporting.get(
                    "revenue"
                )
            )

            gross_sales += _decimal(
                reporting.get(
                    "gross_sales"
                )
            )

            conversions += int(
                _decimal(
                    reporting.get(
                        "cv"
                    )
                )
            )

            clicks += int(
                _decimal(
                    reporting.get(
                        "total_click"
                    )
                )
            )

        records.append(
            EverflowDailyPerformanceRecord(
                report_date=current,
                currency_code=currency,
                payout=payout,
                revenue=revenue,
                gross_sales=gross_sales,
                conversions=conversions,
                clicks=clicks,
                source_rows=len(rows),
            )
        )

        current += timedelta(
            days=1
        )

    return records