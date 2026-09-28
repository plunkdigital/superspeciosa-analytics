from datetime import date

from superspeciosa_analytics.data_quality import (
    MetaCoverage,
)


def test_complete_meta_coverage():
    coverage = MetaCoverage(
        start=date(2026, 9, 20),
        end=date(2026, 9, 27),
        expected_days=8,
        rows_present=8,
        first_date=date(2026, 9, 20),
        last_date=date(2026, 9, 27),
    )

    assert coverage.has_any_data is True
    assert coverage.complete_daily_coverage is True


def test_incomplete_meta_coverage():
    coverage = MetaCoverage(
        start=date(2026, 9, 20),
        end=date(2026, 9, 27),
        expected_days=8,
        rows_present=3,
        first_date=date(2026, 9, 20),
        last_date=date(2026, 9, 22),
    )

    assert coverage.has_any_data is True
    assert coverage.complete_daily_coverage is False


def test_no_meta_coverage():
    coverage = MetaCoverage(
        start=date(2026, 9, 20),
        end=date(2026, 9, 27),
        expected_days=8,
        rows_present=0,
        first_date=None,
        last_date=None,
    )

    assert coverage.has_any_data is False
    assert coverage.complete_daily_coverage is False