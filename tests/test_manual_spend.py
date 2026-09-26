from decimal import Decimal

import pytest

from superspeciosa_analytics.manual_spend import (
    ManualSpendError,
    parse_manual_spend_row,
)


def valid_row():
    return {
        "record_id": "placement-001",
        "vendor": "Example Media",
        "channel": "newsletter",
        "campaign": "September placement",
        "cost_type": "newsletter placement",
        "amount": "6000.00",
        "currency": "USD",
        "service_start_date": "2026-09-01",
        "service_end_date": "2026-09-30",
        "status": "delivered",
        "reference": "INV-001",
        "notes": "",
    }


def test_parses_manual_spend():
    record = parse_manual_spend_row(
        valid_row()
    )

    assert (
        record.amount
        == Decimal("6000.00")
    )

    assert record.currency_code == "USD"
    assert record.status == "delivered"


def test_rejects_negative_amount():
    row = valid_row()
    row["amount"] = "-1"

    with pytest.raises(
        ManualSpendError,
        match="negative",
    ):
        parse_manual_spend_row(row)


def test_rejects_invalid_service_period():
    row = valid_row()

    row["service_start_date"] = (
        "2026-09-30"
    )

    row["service_end_date"] = (
        "2026-09-01"
    )

    with pytest.raises(
        ManualSpendError,
        match="before",
    ):
        parse_manual_spend_row(row)


def test_rejects_unknown_status():
    row = valid_row()
    row["status"] = "paid"

    with pytest.raises(
        ManualSpendError,
        match="Invalid status",
    ):
        parse_manual_spend_row(row)