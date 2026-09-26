import argparse
from datetime import UTC, datetime, time

from sqlalchemy import text

from superspeciosa_analytics.database import engine


def parse_date(value: str) -> datetime:
    parsed = datetime.strptime(
        value,
        "%Y-%m-%d",
    ).date()

    return datetime.combine(
        parsed,
        time.min,
        tzinfo=UTC,
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
    help="End date exclusive, YYYY-MM-DD",
)

args = parser.parse_args()

start = parse_date(args.start)
end = parse_date(args.end)


QUERY = text(
    """
    SELECT
        customer_classification,

        COUNT(*) AS order_count,

        COUNT(
            DISTINCT customer_identity
        ) AS customer_count,

        SUM(product_revenue)
            AS product_revenue

    FROM reporting_order_classification

    WHERE
        reporting_order_at >= :start
        AND reporting_order_at < :end

    GROUP BY customer_classification

    ORDER BY customer_classification
    """
)


with engine.connect() as connection:
    rows = connection.execute(
        QUERY,
        {
            "start": start,
            "end": end,
        },
    ).mappings().all()


print(
    f"Customer mix: "
    f"{args.start} through {args.end} exclusive"
)

print("=" * 70)

for row in rows:
    print()
    print(
        row["customer_classification"].upper()
    )

    print(
        "  Customers:",
        row["customer_count"],
    )

    print(
        "  Orders:",
        row["order_count"],
    )

    print(
        "  Product revenue:",
        row["product_revenue"],
    )