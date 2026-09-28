import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from superspeciosa_analytics.meta import (
    ad_account_path,
    get,
    get_ad_account_id,
)


@dataclass(frozen=True)
class MetaDailySpendRecord:
    ad_account_id: str
    report_date: date
    currency_code: str
    spend: Decimal
    impressions: int
    clicks: int


def fetch_daily_spend(
    *,
    start: date,
    end: date,
) -> list[MetaDailySpendRecord]:
    """
    Fetch account-level daily Meta performance.

    start is inclusive.
    end is exclusive.
    """
    if start >= end:
        raise ValueError(
            "Start date must be before end date."
        )

    account = get(
        ad_account_path(),
        params={
            "fields": (
                "id,"
                "currency,"
                "timezone_name"
            ),
        },
    )

    currency_code = account["currency"]

    meta_until = end - timedelta(days=1)

    payload = get(
        ad_account_path("insights"),
        params={
            "fields": (
                "account_id,"
                "date_start,"
                "date_stop,"
                "spend,"
                "impressions,"
                "clicks"
            ),
            "level": "account",
            "time_increment": 1,
            "time_range": json.dumps(
                {
                    "since": start.isoformat(),
                    "until": meta_until.isoformat(),
                }
            ),
            "limit": 500,
        },
    )

    records = []

    for row in payload.get("data", []):
        records.append(
            MetaDailySpendRecord(
                ad_account_id=(
                    row.get("account_id")
                    or get_ad_account_id()
                ),
                report_date=date.fromisoformat(
                    row["date_start"]
                ),
                currency_code=currency_code,
                spend=Decimal(
                    row.get("spend", "0")
                ),
                impressions=int(
                    row.get("impressions", "0")
                ),
                clicks=int(
                    row.get("clicks", "0")
                ),
            )
        )

    return records