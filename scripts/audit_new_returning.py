from collections import Counter, defaultdict
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.customer_identity import (
    OrderCustomerClassification,
    classify_customer_order,
    resolve_customer_identity,
)
from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Customer, Order


ZERO = Decimal("0")


with SessionLocal() as session:
    statement = (
        select(
            Order.shopify_order_name,
            Order.reporting_order_at,
            Order.source_system,
            Order.woo_customer_id,
            Order.product_revenue,
            Customer.shopify_customer_id,
            Customer.woo_customer_id,
        )
        .outerjoin(
            Customer,
            Order.customer_id == Customer.id,
        )
        .where(
            Order.has_successful_payment.is_(True)
        )
        .where(
            Order.is_test.is_(False)
        )
        .where(
            Order.cancelled_at.is_(None)
        )
        .where(
            Order.product_revenue > ZERO
        )
        .where(
            Order.reporting_order_at.is_not(None)
        )
        .order_by(
            Order.reporting_order_at,
            Order.id,
        )
        .execution_options(
            yield_per=5000
        )
    )

    rows = session.execute(statement)

    seen_identities: set[str] = set()

    classification_counts = Counter()
    identity_method_counts = Counter()

    yearly_counts = defaultdict(Counter)

    total_revenue = Counter()

    unresolved_examples = []

    for (
        order_name,
        reporting_order_at,
        source_system,
        order_woo_customer_id,
        product_revenue,
        shopify_customer_id,
        customer_woo_customer_id,
    ) in rows:
        (
            identity_key,
            identity_method,
        ) = resolve_customer_identity(
            source_system=source_system,
            order_woo_customer_id=(
                order_woo_customer_id
            ),
            shopify_customer_id=(
                shopify_customer_id
            ),
            customer_woo_customer_id=(
                customer_woo_customer_id
            ),
        )

        classification = classify_customer_order(
            identity_key=identity_key,
            seen_identities=seen_identities,
        )

        classification_counts[
            classification
        ] += 1

        identity_method_counts[
            identity_method
        ] += 1

        yearly_counts[
            reporting_order_at.year
        ][classification] += 1

        total_revenue[
            classification
        ] += product_revenue

        if (
            classification
            == OrderCustomerClassification.UNRESOLVED
            and len(unresolved_examples) < 20
        ):
            unresolved_examples.append(
                (
                    order_name,
                    reporting_order_at,
                    source_system,
                )
            )


print("NEW VS RETURNING AUDIT")
print("=" * 70)

print()
print("FULL HISTORY")
print("-" * 70)

print(
    "New customer orders:",
    classification_counts[
        OrderCustomerClassification.NEW
    ],
)

print(
    "Returning customer orders:",
    classification_counts[
        OrderCustomerClassification.RETURNING
    ],
)

print(
    "Unresolved orders:",
    classification_counts[
        OrderCustomerClassification.UNRESOLVED
    ],
)

print(
    "Resolved customer identities:",
    len(seen_identities),
)


print()
print("REVENUE")
print("-" * 70)

print(
    "New customer order revenue:",
    total_revenue[
        OrderCustomerClassification.NEW
    ],
)

print(
    "Returning customer order revenue:",
    total_revenue[
        OrderCustomerClassification.RETURNING
    ],
)

print(
    "Unresolved order revenue:",
    total_revenue[
        OrderCustomerClassification.UNRESOLVED
    ],
)


print()
print("IDENTITY METHODS")
print("-" * 70)

for method, count in sorted(
    identity_method_counts.items(),
    key=lambda item: item[0].value,
):
    print(
        f"{method.value}: {count}"
    )


print()
print("ANNUAL ORDER CLASSIFICATION")
print("-" * 70)

print(
    f"{'Year':<8}"
    f"{'New':>12}"
    f"{'Returning':>14}"
    f"{'Unresolved':>14}"
)

for year in sorted(yearly_counts):
    counts = yearly_counts[year]

    print(
        f"{year:<8}"
        f"{counts[OrderCustomerClassification.NEW]:>12}"
        f"{counts[OrderCustomerClassification.RETURNING]:>14}"
        f"{counts[OrderCustomerClassification.UNRESOLVED]:>14}"
    )


if unresolved_examples:
    print()
    print("UNRESOLVED EXAMPLES")
    print("-" * 70)

    for (
        order_name,
        reporting_order_at,
        source_system,
    ) in unresolved_examples:
        print(
            order_name,
            "|",
            reporting_order_at,
            "|",
            source_system,
        )