import json
from decimal import Decimal

from superspeciosa_analytics.meta import (
    ad_account_path,
    get,
)


START = "2026-09-20"
END = "2026-09-27"


account = get(
    ad_account_path(),
    params={
        "fields": (
            "id,"
            "name,"
            "business_name,"
            "currency,"
            "timezone_name"
        ),
    },
)


print("META ACCOUNT")
print("=" * 70)

print("ID:", account.get("id"))
print("Name:", account.get("name"))
print("Business:", account.get("business_name"))
print("Currency:", account.get("currency"))
print("Timezone:", account.get("timezone_name"))


time_range = json.dumps(
    {
        "since": START,
        "until": END,
    }
)


daily = get(
    ad_account_path("insights"),
    params={
        "fields": (
            "account_id,"
            "account_name,"
            "date_start,"
            "date_stop,"
            "spend,"
            "impressions,"
            "clicks"
        ),
        "level": "account",
        "time_range": time_range,
        "time_increment": 1,
        "limit": 100,
    },
)


daily_rows = daily.get(
    "data",
    [],
)


daily_spend = sum(
    (
        Decimal(
            row.get("spend", "0")
        )
        for row in daily_rows
    ),
    Decimal("0"),
)


print()
print("DAILY API RESULTS")
print("=" * 70)

for row in daily_rows:
    print(
        row.get("date_start"),
        "|",
        row.get("account_id"),
        "|",
        row.get("account_name"),
        "| spend:",
        row.get("spend"),
    )


print()
print(
    "Daily row count:",
    len(daily_rows),
)

print(
    "Daily spend sum:",
    daily_spend,
)


all_days = get(
    ad_account_path("insights"),
    params={
        "fields": (
            "account_id,"
            "account_name,"
            "date_start,"
            "date_stop,"
            "spend,"
            "impressions,"
            "clicks"
        ),
        "level": "account",
        "time_range": time_range,
        "time_increment": "all_days",
        "limit": 100,
    },
)


all_days_rows = all_days.get(
    "data",
    [],
)


print()
print("ALL-DAYS API RESULT")
print("=" * 70)

for row in all_days_rows:
    print(
        "Account:",
        row.get("account_id"),
    )

    print(
        "Name:",
        row.get("account_name"),
    )

    print(
        "Dates:",
        row.get("date_start"),
        "to",
        row.get("date_stop"),
    )

    print(
        "Spend:",
        row.get("spend"),
    )

    print(
        "Impressions:",
        row.get("impressions"),
    )

    print(
        "Clicks:",
        row.get("clicks"),
    )