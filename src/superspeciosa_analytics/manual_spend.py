from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


VALID_STATUSES = {
    "planned",
    "approved",
    "delivered",
    "cancelled",
}


class ManualSpendError(ValueError):
    pass


@dataclass(frozen=True)
class ManualSpendRecord:
    record_id: str
    vendor: str
    channel: str
    campaign: str | None
    cost_type: str
    amount: Decimal
    currency_code: str
    service_start_date: date
    service_end_date: date
    status: str
    reference: str | None
    notes: str | None


def _optional(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value or None


def parse_manual_spend_row(
    row: dict[str, str],
) -> ManualSpendRecord:
    try:
        amount = Decimal(
            row["amount"].strip()
        )
    except (
        KeyError,
        InvalidOperation,
    ) as error:
        raise ManualSpendError(
            "Invalid amount"
        ) from error

    if amount < 0:
        raise ManualSpendError(
            "Amount cannot be negative"
        )

    try:
        start = date.fromisoformat(
            row["service_start_date"].strip()
        )

        end = date.fromisoformat(
            row["service_end_date"].strip()
        )
    except (KeyError, ValueError) as error:
        raise ManualSpendError(
            "Invalid service date"
        ) from error

    if end < start:
        raise ManualSpendError(
            "service_end_date cannot be "
            "before service_start_date"
        )

    status = row["status"].strip().lower()

    if status not in VALID_STATUSES:
        raise ManualSpendError(
            f"Invalid status: {status}"
        )

    currency = row[
        "currency"
    ].strip().upper()

    if len(currency) != 3:
        raise ManualSpendError(
            "Currency must be a 3-letter code"
        )

    required = {
        "record_id": row["record_id"].strip(),
        "vendor": row["vendor"].strip(),
        "channel": row["channel"].strip(),
        "cost_type": row["cost_type"].strip(),
    }

    for field, value in required.items():
        if not value:
            raise ManualSpendError(
                f"{field} is required"
            )

    return ManualSpendRecord(
        record_id=required["record_id"],
        vendor=required["vendor"],
        channel=required["channel"],
        campaign=_optional(
            row.get("campaign")
        ),
        cost_type=required["cost_type"],
        amount=amount,
        currency_code=currency,
        service_start_date=start,
        service_end_date=end,
        status=status,
        reference=_optional(
            row.get("reference")
        ),
        notes=_optional(
            row.get("notes")
        ),
    )