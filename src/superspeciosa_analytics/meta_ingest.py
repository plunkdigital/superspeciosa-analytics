from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from superspeciosa_analytics.meta_insights import (
    MetaDailySpendRecord,
)
from superspeciosa_analytics.models import (
    MetaDailyCoverage,
    MetaDailySpend,
)


def upsert_meta_daily_spend(
    session: Session,
    records: list[MetaDailySpendRecord],
) -> int:
    if not records:
        return 0

    account_ids = {
        record.ad_account_id
        for record in records
    }

    if len(account_ids) != 1:
        raise ValueError(
            "Expected one Meta ad account per import."
        )

    account_id = next(
        iter(account_ids)
    )

    dates = {
        record.report_date
        for record in records
    }

    existing = {
        row.report_date: row
        for row in session.scalars(
            select(MetaDailySpend)
            .where(
                MetaDailySpend.ad_account_id
                == account_id
            )
            .where(
                MetaDailySpend.report_date.in_(
                    dates
                )
            )
        ).all()
    }

    now = datetime.now(UTC)
    created = 0

    for record in records:
        row = existing.get(
            record.report_date
        )

        if row is None:
            row = MetaDailySpend(
                ad_account_id=(
                    record.ad_account_id
                ),
                report_date=(
                    record.report_date
                ),
            )

            session.add(row)

            existing[
                record.report_date
            ] = row

            created += 1

        row.currency_code = (
            record.currency_code
        )
        row.spend = record.spend
        row.impressions = (
            record.impressions
        )
        row.clicks = record.clicks
        row.ingested_at = now

    return created

def mark_meta_daily_coverage(
    session: Session,
    *,
    ad_account_id: str,
    start: date,
    end: date,
) -> None:
    """
    Mark every date in [start, end) as successfully
    checked against the Meta API.

    Existing coverage rows have checked_at refreshed.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    dates = []

    current = start

    while current < end:
        dates.append(current)
        current += timedelta(days=1)

    existing_rows = {
        row.report_date: row
        for row in session.scalars(
            select(
                MetaDailyCoverage
            )
            .where(
                MetaDailyCoverage.ad_account_id
                == ad_account_id
            )
            .where(
                MetaDailyCoverage.report_date.in_(
                    dates
                )
            )
        ).all()
    }

    now = datetime.now(UTC)

    for report_date in dates:
        existing = existing_rows.get(
            report_date
        )

        if existing is not None:
            existing.checked_at = now
            continue

        session.add(
            MetaDailyCoverage(
                ad_account_id=ad_account_id,
                report_date=report_date,
                checked_at=now,
            )
        )