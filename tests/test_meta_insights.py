import json
from datetime import date
from decimal import Decimal

from superspeciosa_analytics.meta_insights import (
    fetch_daily_spend,
)


def test_fetch_daily_spend_uses_exclusive_end(
    monkeypatch,
):
    calls = []

    def fake_get(path, params=None):
        calls.append(
            (path, params)
        )

        if path == "act_123":
            return {
                "id": "act_123",
                "currency": "USD",
                "timezone_name": (
                    "America/New_York"
                ),
            }

        return {
            "data": [
                {
                    "account_id": "123",
                    "date_start": "2026-08-01",
                    "date_stop": "2026-08-01",
                    "spend": "123.45",
                    "impressions": "1000",
                    "clicks": "50",
                }
            ]
        }

    monkeypatch.setenv(
        "META_AD_ACCOUNT_ID",
        "123",
    )

    monkeypatch.setattr(
        "superspeciosa_analytics."
        "meta_insights.get",
        fake_get,
    )

    records = fetch_daily_spend(
        start=date(2026, 8, 1),
        end=date(2026, 8, 8),
    )

    assert len(records) == 1

    assert (
        records[0].spend
        == Decimal("123.45")
    )

    assert (
        records[0].impressions
        == 1000
    )

    assert records[0].clicks == 50

    time_range = json.loads(
        calls[1][1]["time_range"]
    )

    assert time_range == {
        "since": "2026-08-01",
        "until": "2026-08-07",
    }