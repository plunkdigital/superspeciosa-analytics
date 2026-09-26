"""add customer order classification view

Revision ID: 6092a7f5551e
Revises: 96c9bba4cfa2
Create Date: 2026-09-26 07:20:49.564415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6092a7f5551e'
down_revision: Union[str, Sequence[str], None] = '96c9bba4cfa2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW reporting_order_classification AS

        WITH qualifying AS (
            SELECT
                o.id AS order_id,
                o.shopify_order_id,
                o.shopify_order_name,
                o.reporting_order_at,
                o.product_revenue,
                o.source_system,

                CASE
                    WHEN
                        o.source_system = 'woocommerce'
                        AND o.woo_customer_id IS NOT NULL
                        AND o.woo_customer_id <> '0'
                    THEN
                        'woo:' || o.woo_customer_id

                    WHEN
                        c.woo_customer_id IS NOT NULL
                        AND c.woo_customer_id <> '0'
                    THEN
                        'woo:' || c.woo_customer_id

                    WHEN
                        c.shopify_customer_id IS NOT NULL
                    THEN
                        'shopify:' || c.shopify_customer_id

                    ELSE NULL
                END AS customer_identity,

                CASE
                    WHEN
                        o.source_system = 'woocommerce'
                        AND o.woo_customer_id IS NOT NULL
                        AND o.woo_customer_id <> '0'
                    THEN 'woo_order'

                    WHEN
                        c.woo_customer_id IS NOT NULL
                        AND c.woo_customer_id <> '0'
                    THEN 'woo_customer'

                    WHEN
                        c.shopify_customer_id IS NOT NULL
                    THEN 'shopify_customer'

                    ELSE 'unresolved'
                END AS identity_method

            FROM orders AS o

            LEFT JOIN customers AS c
                ON c.id = o.customer_id

            WHERE
                o.has_successful_payment IS TRUE
                AND o.is_test IS FALSE
                AND o.cancelled_at IS NULL
                AND o.product_revenue > 0
                AND o.reporting_order_at IS NOT NULL
        ),

        ranked AS (
            SELECT
                qualifying.*,

                CASE
                    WHEN customer_identity IS NULL
                    THEN NULL

                    ELSE ROW_NUMBER() OVER (
                        PARTITION BY customer_identity
                        ORDER BY
                            reporting_order_at,
                            order_id
                    )
                END AS customer_order_number

            FROM qualifying
        )

        SELECT
            order_id,
            shopify_order_id,
            shopify_order_name,
            reporting_order_at,
            product_revenue,
            source_system,
            customer_identity,
            identity_method,
            customer_order_number,

            CASE
                WHEN customer_identity IS NULL
                THEN 'unresolved'

                WHEN customer_order_number = 1
                THEN 'new'

                ELSE 'returning'
            END AS customer_classification

        FROM ranked
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP VIEW IF EXISTS reporting_order_classification"
    )