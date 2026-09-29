from datetime import date

import pytest

from superspeciosa_analytics.reporting_presets import (
    ComparisonPreset,
    resolve_comparison_preset,
)


AS_OF = date(
    2026,
    9,
    28,
)


def test_yesterday_preset():
    periods = resolve_comparison_preset(
        ComparisonPreset.YESTERDAY,
        as_of=AS_OF,
    )

    assert periods.current_start == date(
        2026,
        9,
        27,
    )

    assert periods.current_end == date(
        2026,
        9,
        28,
    )

    assert periods.previous_start == date(
        2026,
        9,
        26,
    )

    assert periods.previous_end == date(
        2026,
        9,
        27,
    )


def test_last_7_days_preset():
    periods = resolve_comparison_preset(
        ComparisonPreset.LAST_7_DAYS,
        as_of=AS_OF,
    )

    assert periods.current_start == date(
        2026,
        9,
        21,
    )

    assert periods.current_end == date(
        2026,
        9,
        28,
    )

    assert periods.previous_start == date(
        2026,
        9,
        14,
    )

    assert periods.previous_end == date(
        2026,
        9,
        21,
    )


def test_month_to_date_preset():
    periods = resolve_comparison_preset(
        ComparisonPreset.MONTH_TO_DATE,
        as_of=AS_OF,
    )

    assert periods.current_start == date(
        2026,
        9,
        1,
    )

    assert periods.current_end == date(
        2026,
        9,
        28,
    )

    assert periods.previous_start == date(
        2026,
        8,
        1,
    )

    assert periods.previous_end == date(
        2026,
        8,
        28,
    )


def test_month_to_date_on_first_day_rejected():
    with pytest.raises(
        ValueError,
        match="no completed days",
    ):
        resolve_comparison_preset(
            ComparisonPreset.MONTH_TO_DATE,
            as_of=date(
                2026,
                10,
                1,
            ),
        )