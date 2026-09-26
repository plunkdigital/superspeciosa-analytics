import argparse

from superspeciosa_analytics.meta import (
    ad_account_path,
    get,
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--start",
    required=True,
    help="Start date inclusive, YYYY-MM-DD",
)

parser.add_argument(
    "--end",
    required=True,
    help="End date inclusive, YYYY-MM-DD",
)

args = parser.parse_args()


data = get(
    ad_account_path(
        "insights"
    ),
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
        "time_range": (
            "{"
            f'"since":"{args.start}",'
            f'"until":"{args.end}"'
            "}"
        ),
        "time_increment": 1,
    },
)


rows = data.get(
    "data",
    []
)


print("META DAILY SPEND")
print("=" * 70)

for row in rows:
    print(
        row.get("date_start"),
        "| spend:",
        row.get("spend"),
        "| impressions:",
        row.get("impressions"),
        "| clicks:",
        row.get("clicks"),
    )


print()
print(
    "Rows returned:",
    len(rows),
)