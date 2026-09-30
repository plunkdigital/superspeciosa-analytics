import argparse
from datetime import date

import sys
from pathlib import Path

from superspeciosa_analytics.daily_brief import (
    DailyBriefIncompleteDataError,
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

parser.add_argument(
    "--output",
    type=Path,
    help=(
        "Optional path to write the "
        "finished brief."
    ),
)

parser.add_argument(
    "--require-complete-marketing",
    action="store_true",
    help=(
        "Exit with an error if required "
        "marketing source coverage is incomplete."
    ),
)

args = parser.parse_args()


as_of = (
    args.as_of
    if args.as_of is not None
    else current_business_date()
)


try:
    with SessionLocal() as session:
        brief = build_daily_brief(
            session,
            as_of=as_of,
            require_complete_marketing=(
                args.require_complete_marketing
            ),
        )

except DailyBriefIncompleteDataError as exc:
    print(
        f"DAILY BRIEF NOT GENERATED: {exc}",
        file=sys.stderr,
    )

    raise SystemExit(1)


print(brief)


if args.output is not None:
    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        brief + "\n",
        encoding="utf-8",
    )

    print()
    print(
        f"Saved daily brief to: "
        f"{args.output}"
    )