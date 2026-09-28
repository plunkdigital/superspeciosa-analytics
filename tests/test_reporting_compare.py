from decimal import Decimal

from superspeciosa_analytics.reporting_compare import (
    _count_comparison,
    _metric_comparison,
)


def test_metric_comparison():
    result = _metric_comparison(
        Decimal("120"),
        Decimal("100"),
    )

    assert (
        result.absolute_change
        == Decimal("20")
    )

    assert (
        result.percentage_change
        == Decimal("20")
    )


def test_metric_comparison_with_zero_previous():
    result = _metric_comparison(
        Decimal("120"),
        Decimal("0"),
    )

    assert result.percentage_change is None


def test_count_comparison():
    result = _count_comparison(
        90,
        100,
    )

    assert result.absolute_change == -10

    assert (
        result.percentage_change
        == Decimal("-10.0")
    )