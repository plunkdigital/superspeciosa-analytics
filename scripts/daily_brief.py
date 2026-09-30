import argparse
from datetime import date

from superspeciosa_analytics.daily_brief import (
    build_daily_brief,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.reporting_presets import (
    current_business_date,
)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--as-of",
    type=parse_date,
    help=(
        "Exclusive reporting end date. "
        "Defaults to the current business date."
    ),
)

args = parser.parse_args()


as_of = (
    args.as_of
    if args.as_of is not None
    else current_business_date()
)


with SessionLocal() as session:
    brief = build_daily_brief(
        session,
        as_of=as_of,
    )


print(brief)