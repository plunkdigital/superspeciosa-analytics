import argparse
import json
from datetime import date
from pathlib import Path

from superspeciosa_analytics.daily_channel_report import (
    build_daily_channel_report,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting_presets import (
    current_business_date,
)
from superspeciosa_analytics.slack_daily_report import (
    build_daily_slack_payload,
)


def parse_date(
    value: str,
) -> date:
    return date.fromisoformat(value)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--as-of",
    type=parse_date,
)

parser.add_argument(
    "--output",
    type=Path,
    default=Path(
        "data/exports/daily_slack_payload.json"
    ),
)

args = parser.parse_args()


as_of = (
    args.as_of
    if args.as_of is not None
    else current_business_date()
)


with SessionLocal() as session:
    report = build_daily_channel_report(
        session,
        as_of=as_of,
    )


payload = build_daily_slack_payload(
    report
)


args.output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

args.output.write_text(
    json.dumps(
        payload,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)


print(
    "Daily Slack report built:"
)

print(
    args.output
)