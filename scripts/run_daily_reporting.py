import subprocess
import sys
from datetime import date, timedelta

from superspeciosa_analytics.reporting_presets import (
    current_business_date,
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

meta_start = (
    today
    - timedelta(days=3)
)

print()
print("SUPER SPECIOSA DAILY REPORTING PIPELINE")
print("=" * 80)

print(
    f"Business date: {today}"
)

print(
    f"Shopify refresh: "
    f"{shopify_start} through {today} exclusive"
)

print(
    f"Meta refresh: "
    f"{meta_start} through {today} exclusive"
)


run_command(
    [
        sys.executable,
        "scripts/import_shopify_updates.py",
        "--start",
        shopify_start.isoformat(),
        "--end",
        today.isoformat(),
    ]
)


run_command(
    [
        sys.executable,
        "scripts/import_meta_spend.py",
        "--start",
        meta_start.isoformat(),
        "--end",
        today.isoformat(),
    ]
)


for preset in (
    "yesterday",
    "last7",
    "mtd",
):
    run_command(
        [
            sys.executable,
            "scripts/report_comparison.py",
            "--preset",
            preset,
            "--as-of",
            today.isoformat(),
        ]
    )


print()
print("=" * 80)
print("DAILY REPORTING PIPELINE COMPLETE")
print("=" * 80)