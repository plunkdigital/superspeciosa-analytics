from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum

from superspeciosa_analytics.reporting_time import (
    get_reporting_timezone,
)


class ComparisonPreset(StrEnum):
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last7"
    MONTH_TO_DATE = "mtd"


@dataclass(frozen=True)
class ComparisonPeriods:
    current_start: date
    current_end: date
    previous_start: date
    previous_end: date


def current_business_date() -> date:
    return datetime.now(
        get_reporting_timezone()
    ).date()


def _previous_month_start(
    value: date,
) -> date:
    if value.month == 1:
        return date(
            value.year - 1,
            12,
            1,
        )

    return date(
        value.year,
        value.month - 1,
        1,
    )


def _next_month_start(
    value: date,
) -> date:
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

def previous_same_weekdays(
    value: date,
    *,
    count: int = 4,
) -> tuple[date, ...]:
    if count <= 0:
        raise ValueError(
            "Count must be positive."
        )

    return tuple(
        value
        - timedelta(
            days=7 * offset
        )
        for offset in range(
            1,
            count + 1,
        )
    )


def resolve_comparison_preset(
    preset: ComparisonPreset | str,
    *,
    as_of: date | None = None,
) -> ComparisonPeriods:
    """
    as_of is the exclusive end date.

    Example:
        as_of=2026-09-28 means completed data
        through 2026-09-27.
    """
    preset = ComparisonPreset(preset)

    if as_of is None:
        as_of = current_business_date()

    if preset == ComparisonPreset.YESTERDAY:
        current_end = as_of
        current_start = (
            current_end
            - timedelta(days=1)
        )

        previous_end = current_start
        previous_start = (
            previous_end
            - timedelta(days=1)
        )

    elif preset == ComparisonPreset.LAST_7_DAYS:
        current_end = as_of
        current_start = (
            current_end
            - timedelta(days=7)
        )

        previous_end = current_start
        previous_start = (
            previous_end
            - timedelta(days=7)
        )

    else:
        current_start = date(
            as_of.year,
            as_of.month,
            1,
        )

        current_end = as_of

        completed_days = (
            current_end
            - current_start
        ).days

        if completed_days <= 0:
            raise ValueError(
                "Month-to-date has no completed days."
            )

        previous_start = (
            _previous_month_start(
                current_start
            )
        )

        previous_month_end = (
            _next_month_start(
                previous_start
            )
        )

        requested_previous_end = (
            previous_start
            + timedelta(
                days=completed_days
            )
        )

        previous_end = min(
            requested_previous_end,
            previous_month_end,
        )

    return ComparisonPeriods(
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )