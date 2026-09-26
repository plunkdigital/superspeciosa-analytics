from sqlalchemy import text

from superspeciosa_analytics.database import engine


QUERY = """
SELECT
    customer_classification,
    COUNT(*) AS order_count,
    COUNT(DISTINCT customer_identity)
        AS customer_count,
    SUM(product_revenue)
        AS product_revenue

FROM reporting_order_classification

GROUP BY customer_classification

ORDER BY customer_classification
"""


with engine.connect() as connection:
    rows = connection.execute(
        text(QUERY)
    ).mappings().all()


print("CUSTOMER CLASSIFICATION VIEW")
print("=" * 70)

total_orders = 0

for row in rows:
    print()
    print(
        row["customer_classification"]
    )

    print(
        "  Orders:",
        row["order_count"],
    )

    print(
        "  Customers:",
        row["customer_count"],
    )

    print(
        "  Revenue:",
        row["product_revenue"],
    )

    total_orders += row["order_count"]


print()
print("Total qualifying orders:", total_orders)