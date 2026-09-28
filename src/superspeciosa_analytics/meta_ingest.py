from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from superspeciosa_analytics.meta_insights import (
    MetaDailySpendRecord,
)
from superspeciosa_analytics.models import (
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