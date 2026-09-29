from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from superspeciosa_analytics.everflow_reporting import (
    EverflowDailyPerformanceRecord,
)
from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
)


def upsert_everflow_daily_performance(
    session: Session,
    records: list[
        EverflowDailyPerformanceRecord
    ],
) -> int:
    if not records:
        return 0

    dates = [
        record.report_date
        for record in records
    ]

    existing = {
        row.report_date: row
        for row in session.scalars(
            select(
                EverflowDailyPerformance
            )
            .where(
                EverflowDailyPerformance.report_date.in_(
                    dates
                )
            )
        ).all()
    }

    created = 0
    now = datetime.now(UTC)

    for record in records:
        row = existing.get(
            record.report_date
        )

        if row is None:
            row = EverflowDailyPerformance(
                report_date=record.report_date,
                currency_code=record.currency_code,
                payout=record.payout,
                revenue=record.revenue,
                gross_sales=record.gross_sales,
                conversions=record.conversions,
                clicks=record.clicks,
                source_rows=record.source_rows,
                ingested_at=now,
            )

            session.add(row)
            created += 1

        else:
            row.currency_code = (
                record.currency_code
            )
            row.payout = record.payout
            row.revenue = record.revenue
            row.gross_sales = (
                record.gross_sales
            )
            row.conversions = (
                record.conversions
            )
            row.clicks = record.clicks
            row.source_rows = (
                record.source_rows
            )
            row.ingested_at = now

    return created