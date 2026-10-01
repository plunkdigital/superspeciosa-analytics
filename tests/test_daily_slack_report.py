from datetime import date
from decimal import Decimal

from superspeciosa_analytics.reporting_presets import (
    previous_same_weekdays,
)
from superspeciosa_analytics.slack_daily_report import (
    _trend,
)


def test_previous_four_same_weekdays():
    result = previous_same_weekdays(
        date(
            2026,
            9,
            30,
        ),
        count=4,
    )

    assert result == (
        date(2026, 9, 23),
        date(2026, 9, 16),
        date(2026, 9, 9),
        date(2026, 9, 2),
    )


def test_higher_revenue_is_good():
    result = _trend(
        Decimal("110"),
        Decimal("100"),
        higher_is_better=True,
    )

    assert result.startswith(
        "🟢"
    )


def test_lower_revenue_is_bad():
    result = _trend(
        Decimal("90"),
        Decimal("100"),
        higher_is_better=True,
    )

    assert result.startswith(
        "🔴"
    )


def test_lower_cac_is_good():
    result = _trend(
        Decimal("90"),
        Decimal("100"),
        higher_is_better=False,
    )

    assert result.startswith(
        "🟢"
    )


def test_higher_cac_is_bad():
    result = _trend(
        Decimal("110"),
        Decimal("100"),
        higher_is_better=False,
    )

    assert result.startswith(
        "🔴"
    )