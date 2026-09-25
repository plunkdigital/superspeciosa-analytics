import argparse
import subprocess
import sys
from datetime import date


def parse_month(value: str) -> date:
    try:
        year, month = value.split("-")

        return date(
            int(year),
            int(month),
            1,
        )

    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(
            "Month must be YYYY-MM"
        )


def next_month(value: date) -> date:
    if value.month == 12:
        return date(
            value.year + 1,
            1,
            1,
        )

    return date(
        value.year,
        value.month + 1,
        1,
    )


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    type=parse_month,
    help="First month inclusive, YYYY-MM",
)

parser.add_argument(
    "--end",
    required=True,
    type=parse_month,
    help="End month exclusive, YYYY-MM",
)

args = parser.parse_args()

if args.start >= args.end:
    raise SystemExit(
        "--start must be before --end"
    )


current = args.start

months = []

while current < args.end:
    months.append(current)
    current = next_month(current)


print(
    f"Monthly backfill: "
    f"{args.start:%Y-%m} through "
    f"{args.end:%Y-%m} exclusive"
)

print(
    f"Months to process: {len(months)}"
)

print()


for index, month_start in enumerate(
    months,
    start=1,
):
    month_end = next_month(
        month_start
    )

    start_value = (
        month_start.isoformat()
    )

    end_value = (
        month_end.isoformat()
    )

    print()
    print("=" * 70)

    print(
        f"MONTH {index}/{len(months)}: "
        f"{month_start:%Y-%m}"
    )

    print("=" * 70)

    subprocess.run(
        [
            sys.executable,
            "scripts/import_shopify_range.py",
            "--start",
            start_value,
            "--end",
            end_value,
        ],
        check=True,
    )


print()
print("=" * 70)
print("MONTHLY BACKFILL COMPLETE")
print("=" * 70)