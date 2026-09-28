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

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Month must be YYYY-MM"
        ) from error


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


months = []
current = args.start

while current < args.end:
    months.append(current)
    current = next_month(current)


print(
    f"Meta monthly backfill: "
    f"{args.start:%Y-%m} through "
    f"{args.end:%Y-%m} exclusive"
)

print(
    f"Months to process: {len(months)}"
)


for index, month_start in enumerate(
    months,
    start=1,
):
    month_end = next_month(
        month_start
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
            "scripts/import_meta_spend.py",
            "--start",
            month_start.isoformat(),
            "--end",
            month_end.isoformat(),
        ],
        check=True,
    )


print()
print("=" * 70)
print("META MONTHLY BACKFILL COMPLETE")
print("=" * 70)