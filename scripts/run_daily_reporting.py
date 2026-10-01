import subprocess
import sys
from datetime import date, timedelta

from superspeciosa_analytics.reporting_presets import (
    current_business_date,
    previous_same_weekdays,
)


def run_command(command: list[str]) -> None:
    print()
    print("=" * 80)
    print("RUNNING")
    print(" ".join(command))
    print("=" * 80)

    result = subprocess.run(
        command,
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"Command failed with exit code "
            f"{result.returncode}: "
            f"{' '.join(command)}"
        )


today = current_business_date()

shopify_start = (
    today
    - timedelta(days=3)
)

shopify_end = (
    today
    + timedelta(days=1)
)

marketing_start = (
    today
    - timedelta(days=7)
)

print()
print("SUPER SPECIOSA DAILY REPORTING PIPELINE")
print("=" * 80)

print(
    f"Business date: {today}"
)

print(
    f"Shopify refresh: "
    f"{shopify_start} through "
    f"{shopify_end} exclusive"
)

print(
    f"Marketing refresh: "
    f"{marketing_start} through {today} exclusive"
)


run_command(
    [
        sys.executable,
        "scripts/import_shopify_updates.py",
        "--start",
        shopify_start.isoformat(),
        "--end",
        shopify_end.isoformat(),
    ]
)


run_command(
    [
        sys.executable,
        "scripts/import_meta_spend.py",
        "--start",
        marketing_start.isoformat(),
        "--end",
        today.isoformat(),
    ]
)

run_command(
    [
        sys.executable,
        "scripts/import_everflow.py",
        "--start",
        marketing_start.isoformat(),
        "--end",
        today.isoformat(),
    ]
)

run_command(
    [
        sys.executable,
        "scripts/import_thoughtmetric.py",
        "--start",
        marketing_start.isoformat(),
        "--end",
        today.isoformat(),
    ]
)

thoughtmetric_report_date = (
    today
    - timedelta(days=1)
)

thoughtmetric_baseline_dates = (
    previous_same_weekdays(
        thoughtmetric_report_date,
        count=4,
    )
)


for baseline_date in (
    thoughtmetric_baseline_dates
):
    baseline_end = (
        baseline_date
        + timedelta(days=1)
    )

    run_command(
        [
            sys.executable,
            "scripts/import_thoughtmetric.py",
            "--start",
            baseline_date.isoformat(),
            "--end",
            baseline_end.isoformat(),
        ]
    )


run_command(
    [
        sys.executable,
        "scripts/build_daily_slack_report.py",
        "--as-of",
        today.isoformat(),
        "--output",
        "data/exports/daily_slack_payload.json",
    ]
)


print()
print("=" * 80)
print("DAILY REPORTING PIPELINE COMPLETE")
print("=" * 80)