import argparse
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.models import (
    ThoughtMetricDailyChannel,
    ThoughtMetricDailyCoverage,
)
from superspeciosa_analytics.thoughtmetric_ingest import (
    replace_thoughtmetric_daily_channels,
)
from superspeciosa_analytics.thoughtmetric_reporting import (
    fetch_daily_channel_performance,
)


ZERO = Decimal("0")


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    type=parse_date,
)

parser.add_argument(
    "--end",
    required=True,
    type=parse_date,
)

args = parser.parse_args()


print()
print("THOUGHTMETRIC DAILY ATTRIBUTION IMPORT")
print("=" * 72)

print(
    f"Period: {args.start} "
    f"through {args.end} exclusive"
)

print(
    "Attribution model:",
    "ThoughtMetric project default",
)


records, checked_dates = (
    fetch_daily_channel_performance(
        start=args.start,
        end=args.end,
    )
)


print(
    "Days checked:",
    len(checked_dates),
)

print(
    "Channel rows fetched:",
    len(records),
)


source_orders = sum(
    (
        row.orders
        for row in records
    ),
    ZERO,
)

source_new_customers = sum(
    (
        row.new_customer_orders
        for row in records
    ),
    ZERO,
)

source_sales = sum(
    (
        row.attributed_total_sales
        for row in records
    ),
    ZERO,
)


with SessionLocal() as session:
    replace_thoughtmetric_daily_channels(
        session,
        records=records,
        checked_dates=checked_dates,
    )

    session.commit()

    db_rows = session.scalars(
        select(
            ThoughtMetricDailyChannel
        )
        .where(
            ThoughtMetricDailyChannel.report_date
            >= args.start
        )
        .where(
            ThoughtMetricDailyChannel.report_date
            < args.end
        )
    ).all()

    coverage_rows = session.scalars(
        select(
            ThoughtMetricDailyCoverage
        )
        .where(
            ThoughtMetricDailyCoverage.report_date
            >= args.start
        )
        .where(
            ThoughtMetricDailyCoverage.report_date
            < args.end
        )
    ).all()


db_orders = sum(
    (
        row.orders
        for row in db_rows
    ),
    ZERO,
)

db_new_customers = sum(
    (
        row.new_customer_orders
        for row in db_rows
    ),
    ZERO,
)

db_sales = sum(
    (
        row.attributed_total_sales
        for row in db_rows
    ),
    ZERO,
)


print()
print("RECONCILIATION")
print("-" * 72)

print(
    f"Coverage days: "
    f"{len(coverage_rows)} DB "
    f"/ {len(checked_dates)} ThoughtMetric"
)

print(
    f"Channel rows: "
    f"{len(db_rows)} DB "
    f"/ {len(records)} ThoughtMetric"
)

print(
    f"Orders: "
    f"{db_orders} DB "
    f"/ {source_orders} ThoughtMetric"
)

print(
    f"New customer orders: "
    f"{db_new_customers} DB "
    f"/ {source_new_customers} ThoughtMetric"
)

print(
    f"Attributed sales: "
    f"{db_sales} DB "
    f"/ {source_sales} ThoughtMetric"
)


failures = []

if len(coverage_rows) != len(
    checked_dates
):
    failures.append(
        "Coverage-day mismatch"
    )

if len(db_rows) != len(records):
    failures.append(
        "Channel-row mismatch"
    )

if db_orders != source_orders:
    failures.append(
        "Order attribution mismatch"
    )

if (
    db_new_customers
    != source_new_customers
):
    failures.append(
        "New-customer attribution mismatch"
    )

if db_sales != source_sales:
    failures.append(
        "Attributed-sales mismatch"
    )


if failures:
    print()
    print(
        "RECONCILIATION FAILED"
    )

    for failure in failures:
        print(
            f"- {failure}"
        )

    raise SystemExit(1)


print()
print(
    "ThoughtMetric daily attribution "
    "reconciliation passed."
)