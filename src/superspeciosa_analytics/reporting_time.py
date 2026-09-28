import os
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


load_dotenv()


def get_reporting_timezone() -> ZoneInfo:
    name = os.getenv(
        "REPORTING_TIMEZONE",
        "America/New_York",
    )

    return ZoneInfo(name)


def reporting_date_range_to_utc(
    *,
    start: date,
    end: date,
) -> tuple[datetime, datetime]:
    """
    Convert a business-date range into UTC timestamps.

    start is inclusive.
    end is exclusive.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    timezone = get_reporting_timezone()

    local_start = datetime.combine(
        start,
        time.min,
        tzinfo=timezone,
    )

    local_end = datetime.combine(
        end,
        time.min,
        tzinfo=timezone,
    )

    return (
        local_start.astimezone(UTC),
        local_end.astimezone(UTC),
    )