from datetime import timedelta

from superspeciosa_analytics.everflow import (
    get,
    get_currency,
    get_timezone_id,
    post,
)
from superspeciosa_analytics.reporting_presets import (
    current_business_date,
)


timezones = get(
    "/meta/timezones"
).get(
    "timezones",
    [],
)


configured_timezone_id = (
    get_timezone_id()
)


new_york = None

for timezone in timezones:
    timezone_name = str(
        timezone.get(
            "timezone",
            ""
        )
    )

    if (
        timezone_name
        == "America/New_York"
    ):
        new_york = timezone
        break


if configured_timezone_id is not None:
    timezone_id = (
        configured_timezone_id
    )

elif new_york is not None:
    timezone_id = int(
        new_york["timezone_id"]
    )

else:
    raise RuntimeError(
        "Could not identify the "
        "America/New_York Everflow timezone."
    )


print()
print("EVERFLOW CONNECTION CHECK")
print("=" * 60)

print(
    "Timezone ID:",
    timezone_id,
)

if new_york is not None:
    print(
        "Timezone:",
        new_york.get(
            "timezone"
        ),
    )


today = current_business_date()

yesterday = (
    today
    - timedelta(days=1)
)


report = post(
    "/networks/reporting/entity/table",
    {
        "from": yesterday.isoformat(),
        "to": yesterday.isoformat(),
        "timezone_id": timezone_id,
        "currency_id": get_currency(),
        "columns": [
            {
                "column": "affiliate",
            }
        ],
        "query": {
            "filters": [],
            "exclusions": [],
        },
    },
)


rows = report.get(
    "table",
    [],
)


total_payout = 0.0
total_revenue = 0.0
total_gross_sales = 0.0
total_conversions = 0
total_clicks = 0


for row in rows:
    reporting = row.get(
        "reporting",
        {},
    )

    total_payout += float(
        reporting.get(
            "payout",
            0,
        )
        or 0
    )

    total_revenue += float(
        reporting.get(
            "revenue",
            0,
        )
        or 0
    )

    total_gross_sales += float(
        reporting.get(
            "gross_sales",
            0,
        )
        or 0
    )

    total_conversions += int(
        reporting.get(
            "cv",
            0,
        )
        or 0
    )

    total_clicks += int(
        reporting.get(
            "total_click",
            0,
        )
        or 0
    )


print()
print(
    "Report date:",
    yesterday,
)

print(
    "Affiliate rows:",
    len(rows),
)

print(
    "Payout:",
    f"${total_payout:,.2f}",
)

print(
    "Everflow revenue:",
    f"${total_revenue:,.2f}",
)

print(
    "Gross sales:",
    f"${total_gross_sales:,.2f}",
)

print(
    "Conversions:",
    total_conversions,
)

print(
    "Clicks:",
    total_clicks,
)

print()
print(
    "Everflow connection check passed."
)