from sqlalchemy import text

from superspeciosa_analytics.database import engine


IDENTITIES_QUERY = text(
    """
    SELECT
        customer_identity

    FROM reporting_order_classification

    WHERE
        customer_identity IS NOT NULL

    GROUP BY customer_identity

    HAVING
        COUNT(*) FILTER (
            WHERE source_system = 'woocommerce'
        ) > 0

        AND

        COUNT(*) FILTER (
            WHERE source_system = 'shopify'
        ) > 0

    ORDER BY customer_identity

    LIMIT 20
    """
)


HISTORY_QUERY = text(
    """
    SELECT
        shopify_order_name,
        reporting_order_at,
        source_system,
        customer_order_number,
        customer_classification,
        product_revenue

    FROM reporting_order_classification

    WHERE
        customer_identity = :identity

    ORDER BY
        reporting_order_at,
        order_id
    """
)


with engine.connect() as connection:
    identities = connection.execute(
        IDENTITIES_QUERY
    ).scalars().all()

    for identity in identities:
        print()
        print("=" * 80)
        print(identity)
        print("=" * 80)

        history = connection.execute(
            HISTORY_QUERY,
            {
                "identity": identity,
            },
        ).mappings().all()

        for order in history:
            print(
                order["reporting_order_at"],
                "|",
                order["shopify_order_name"],
                "|",
                order["source_system"],
                "| #",
                order["customer_order_number"],
                "|",
                order["customer_classification"],
                "| $",
                order["product_revenue"],
            )