from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from superspeciosa_analytics.manual_spend import (
    ManualSpendRecord,
)
from superspeciosa_analytics.models import ManualSpend


def upsert_manual_spend(
    session: Session,
    records: list[ManualSpendRecord],
) -> int:
    if not records:
        return 0

    record_ids = {
        record.record_id
        for record in records
    }

    existing = {
        row.record_id: row
        for row in session.scalars(
            select(ManualSpend).where(
                ManualSpend.record_id.in_(
                    record_ids
                )
            )
        ).all()
    }

    now = datetime.now(UTC)
    created = 0

    for record in records:
        row = existing.get(
            record.record_id
        )

        if row is None:
            row = ManualSpend(
                record_id=record.record_id,
                ingested_at=now,
            )

            session.add(row)

            existing[
                record.record_id
            ] = row

            created += 1

        row.vendor = record.vendor
        row.channel = record.channel
        row.campaign = record.campaign
        row.cost_type = record.cost_type
        row.amount = record.amount
        row.currency_code = (
            record.currency_code
        )
        row.service_start_date = (
            record.service_start_date
        )
        row.service_end_date = (
            record.service_end_date
        )
        row.status = record.status
        row.reference = record.reference
        row.notes = record.notes

    return created