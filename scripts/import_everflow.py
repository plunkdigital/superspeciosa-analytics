import argparse
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.everflow_ingest import (
    upsert_everflow_daily_performance,
)
from superspeciosa_analytics.everflow_reporting import (
    fetch_daily_performance,
)
from superspeciosa_analytics.models import (
    EverflowDailyPerformance,
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    type=parse_date,
    help="Start date inclusive, YYYY-MM-DD",
)

parser.add_argument(
    "--end",
    required=True,
    type=parse_date,
    help="End date exclusive, YYYY-MM-DD",
)

args = parser.parse_args()


print()
print("EVERFLOW DAILY PERFORMANCE IMPORT")
print("=" * 60)

print(
    f"Period: {args.start} "
    f"through {args.end} exclusive"
)


records = fetch_daily_performance(
    start=args.start,
    end=args.end,
)


print(
    f"Fetched {len(records)} daily records."
)


source_payout = sum(
    (
        record.payout
        for record in records
    ),
    Decimal("0"),
)

source_revenue = sum(
    (
        record.revenue
        for record in records
    ),
    Decimal("0"),
)

source_gross_sales = sum(
    (
        record.gross_sales
        for record in records
    ),
    Decimal("0"),
)

source_conversions = sum(
    record.conversions
    for record in records
)

source_clicks = sum(
    record.clicks
    for record in records
)


with SessionLocal() as session:
    created = (
        upsert_everflow_daily_performance(
            session,
            records,
        )
    )

    session.commit()

    db_rows = session.scalars(
        select(
            EverflowDailyPerformance
        )
        .where(
            EverflowDailyPerformance.report_date
            >= args.start
        )
        .where(
            EverflowDailyPerformance.report_date
            < args.end
        )
    ).all()


db_payout = sum(
    (
        row.payout
        for row in db_rows
    ),
    Decimal("0"),
)

db_revenue = sum(
    (
        row.revenue
        for row in db_rows
    ),
    Decimal("0"),
)

db_gross_sales = sum(
    (
        row.gross_sales
        for row in db_rows
    ),
    Decimal("0"),
)

db_conversions = sum(
    row.conversions
    for row in db_rows
)

db_clicks = sum(
    row.clicks
    for row in db_rows
)


print()
print(
    f"New daily rows inserted: {created}"
)

print()
print("Reconciliation")
print("-" * 60)

print(
    f"Days: {len(db_rows)} DB "
    f"/ {len(records)} Everflow"
)

print(
    f"Payout: {db_payout} DB "
    f"/ {source_payout} Everflow"
)

print(
    f"Revenue: {db_revenue} DB "
    f"/ {source_revenue} Everflow"
)

print(
    f"Gross sales: {db_gross_sales} DB "
    f"/ {source_gross_sales} Everflow"
)

print(
    f"Conversions: {db_conversions} DB "
    f"/ {source_conversions} Everflow"
)

print(
    f"Clicks: {db_clicks} DB "
    f"/ {source_clicks} Everflow"
)


failures = []

if len(db_rows) != len(records):
    failures.append(
        "Daily row count mismatch"
    )

if db_payout != source_payout:
    failures.append(
        "Payout mismatch"
    )

if db_revenue != source_revenue:
    failures.append(
        "Revenue mismatch"
    )

if db_gross_sales != source_gross_sales:
    failures.append(
        "Gross sales mismatch"
    )

if db_conversions != source_conversions:
    failures.append(
        "Conversion mismatch"
    )

if db_clicks != source_clicks:
    failures.append(
        "Click mismatch"
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
    "Everflow daily performance "
    "reconciliation passed."
)