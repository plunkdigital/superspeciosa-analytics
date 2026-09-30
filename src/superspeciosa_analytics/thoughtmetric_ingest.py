from datetime import UTC, date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from superspeciosa_analytics.models import (
    ThoughtMetricDailyChannel,
    ThoughtMetricDailyCoverage,
)
from superspeciosa_analytics.thoughtmetric_reporting import (
    ThoughtMetricDailyChannelRecord,
)


def replace_thoughtmetric_daily_channels(
    session: Session,
    *,
    records: list[
        ThoughtMetricDailyChannelRecord
    ],
    checked_dates: list[date],
) -> int:
    if not checked_dates:
        return 0

    session.execute(
        delete(
            ThoughtMetricDailyChannel
        ).where(
            ThoughtMetricDailyChannel.report_date.in_(
                checked_dates
            )
        )
    )

    now = datetime.now(UTC)

    for record in records:
        session.add(
            ThoughtMetricDailyChannel(
                report_date=record.report_date,
                channel_key=record.channel_key,
                orders=record.orders,
                new_customer_orders=(
                    record.new_customer_orders
                ),
                new_customer_sales=(
                    record.new_customer_sales
                ),
                attributed_total_sales=(
                    record.attributed_total_sales
                ),
                converted_spend=(
                    record.converted_spend
                ),
                ingested_at=now,
            )
        )

    existing_coverage = {
        row.report_date: row
        for row in session.scalars(
            select(
                ThoughtMetricDailyCoverage
            )
            .where(
                ThoughtMetricDailyCoverage.report_date.in_(
                    checked_dates
                )
            )
        ).all()
    }

    for report_date in checked_dates:
        coverage = (
            existing_coverage.get(
                report_date
            )
        )

        if coverage is None:
            session.add(
                ThoughtMetricDailyCoverage(
                    report_date=report_date,
                    checked_at=now,
                )
            )

        else:
            coverage.checked_at = now

    return len(records)