import argparse
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.meta_ingest import (
    upsert_meta_daily_spend,
)
from superspeciosa_analytics.meta_insights import (
    fetch_daily_spend,
)
from superspeciosa_analytics.models import (
    MetaDailySpend,
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    type=parse_date,
    help="Start date inclusive",
)

parser.add_argument(
    "--end",
    required=True,
    type=parse_date,
    help=(
        "End date exclusive. Example: "
        "2026-09-28 includes data through 2026-09-27."
    ),
)

args = parser.parse_args()


records = fetch_daily_spend(
    start=args.start,
    end=args.end,
)

print(
    f"Fetched {len(records)} Meta daily rows."
)


if not records:
    print(
        "No Meta spend rows returned."
    )
    raise SystemExit(0)


account_id = records[0].ad_account_id

source_dates = {
    record.report_date
    for record in records
}

source_spend = sum(
    (
        record.spend
        for record in records
    ),
    Decimal("0"),
)

source_impressions = sum(
    record.impressions
    for record in records
)

source_clicks = sum(
    record.clicks
    for record in records
)


with SessionLocal() as session:
    created = upsert_meta_daily_spend(
        session,
        records,
    )

    session.commit()

    db_rows = session.scalars(
        select(MetaDailySpend)
        .where(
            MetaDailySpend.ad_account_id
            == account_id
        )
        .where(
            MetaDailySpend.report_date
            >= args.start
        )
        .where(
            MetaDailySpend.report_date
            < args.end
        )
    ).all()


db_dates = {
    row.report_date
    for row in db_rows
}

db_spend = sum(
    (
        row.spend
        for row in db_rows
    ),
    Decimal("0"),
)

db_impressions = sum(
    row.impressions
    for row in db_rows
)

db_clicks = sum(
    row.clicks
    for row in db_rows
)


print()
print(
    "New rows inserted:",
    created,
)

print()
print("RECONCILIATION")
print("-" * 60)

print(
    f"Rows: {len(db_rows)} DB "
    f"/ {len(records)} Meta"
)

print(
    f"Spend: {db_spend} DB "
    f"/ {source_spend} Meta"
)

print(
    f"Impressions: {db_impressions} DB "
    f"/ {source_impressions} Meta"
)

print(
    f"Clicks: {db_clicks} DB "
    f"/ {source_clicks} Meta"
)


failures = []

if db_dates != source_dates:
    failures.append(
        "Report-date mismatch"
    )

if db_spend != source_spend:
    failures.append(
        "Spend mismatch"
    )

if db_impressions != source_impressions:
    failures.append(
        "Impressions mismatch"
    )

if db_clicks != source_clicks:
    failures.append(
        "Clicks mismatch"
    )


if failures:
    print()
    print("RECONCILIATION FAILED")

    for failure in failures:
        print(
            f"- {failure}"
        )

    raise SystemExit(1)


print()
print(
    "Meta daily spend reconciliation passed."
)