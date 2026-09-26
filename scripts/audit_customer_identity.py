from collections import Counter, defaultdict
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Customer, Order


ZERO = Decimal("0")


def is_qualifying(
    has_successful_payment,
    is_test,
    cancelled_at,
    product_revenue,
):
    return (
        has_successful_payment
        and not is_test
        and cancelled_at is None
        and product_revenue > ZERO
    )


with SessionLocal() as session:
    # --------------------------------------------------
    # Customer-level Woo -> Shopify relationships
    # --------------------------------------------------

    woo_to_shopify = defaultdict(set)

    customer_rows = session.execute(
        select(
            Customer.shopify_customer_id,
            Customer.woo_customer_id,
        )
    )

    total_customers = 0
    customers_with_woo_id = 0

    for (
        shopify_customer_id,
        woo_customer_id,
    ) in customer_rows:
        total_customers += 1

        if (
            woo_customer_id is not None
            and woo_customer_id != "0"
        ):
            customers_with_woo_id += 1

            woo_to_shopify[
                woo_customer_id
            ].add(
                shopify_customer_id
            )

    woo_ids_with_multiple_shopify_customers = {
        woo_id: shopify_ids
        for woo_id, shopify_ids
        in woo_to_shopify.items()
        if len(shopify_ids) > 1
    }

    # --------------------------------------------------
    # Order-level relationships
    # --------------------------------------------------

    statement = (
        select(
            Order.shopify_order_name,
            Order.shopify_order_id,
            Order.reporting_order_at,
            Order.source_system,
            Order.woo_customer_id,
            Order.customer_id,
            Customer.shopify_customer_id,
            Customer.woo_customer_id,
            Order.has_successful_payment,
            Order.is_test,
            Order.cancelled_at,
            Order.product_revenue,
        )
        .outerjoin(
            Customer,
            Order.customer_id == Customer.id,
        )
        .order_by(
            Order.reporting_order_at
        )
        .execution_options(
            yield_per=5000
        )
    )

    rows = session.execute(
        statement
    )

    total_orders = 0
    qualifying_orders = 0

    source_counts = Counter()
    qualifying_source_counts = Counter()

    qualifying_with_shopify_customer = 0
    qualifying_without_shopify_customer = 0

    registered_woo_matches = 0
    registered_woo_mismatches = 0

    guest_woo_with_customer_woo_id = 0
    guest_woo_without_customer_woo_id = 0

    shopify_customer_to_order_woo_ids = (
        defaultdict(set)
    )

    mismatch_examples = []
    missing_customer_examples = []

    for row in rows:
        (
            order_name,
            shopify_order_id,
            reporting_order_at,
            source_system,
            order_woo_customer_id,
            customer_id,
            shopify_customer_id,
            customer_woo_customer_id,
            has_successful_payment,
            is_test,
            cancelled_at,
            product_revenue,
        ) = row

        total_orders += 1

        source_counts[
            source_system
        ] += 1

        qualifying = is_qualifying(
            has_successful_payment,
            is_test,
            cancelled_at,
            product_revenue,
        )

        if qualifying:
            qualifying_orders += 1

            qualifying_source_counts[
                source_system
            ] += 1

            if customer_id is None:
                qualifying_without_shopify_customer += 1

                if len(
                    missing_customer_examples
                ) < 20:
                    missing_customer_examples.append(
                        (
                            order_name,
                            reporting_order_at,
                            source_system,
                            order_woo_customer_id,
                        )
                    )

            else:
                qualifying_with_shopify_customer += 1

        # Only WooCommerce-origin orders have a
        # meaningful order-level Woo customer ID.
        if source_system != "woocommerce":
            continue

        if (
            order_woo_customer_id is not None
            and order_woo_customer_id != "0"
        ):
            if shopify_customer_id is not None:
                shopify_customer_to_order_woo_ids[
                    shopify_customer_id
                ].add(
                    order_woo_customer_id
                )

            if (
                customer_woo_customer_id
                == order_woo_customer_id
            ):
                registered_woo_matches += 1

            else:
                registered_woo_mismatches += 1

                if len(mismatch_examples) < 20:
                    mismatch_examples.append(
                        (
                            order_name,
                            reporting_order_at,
                            order_woo_customer_id,
                            customer_woo_customer_id,
                            shopify_customer_id,
                        )
                    )

        elif order_woo_customer_id == "0":
            if (
                customer_woo_customer_id
                is not None
                and customer_woo_customer_id != "0"
            ):
                guest_woo_with_customer_woo_id += 1
            else:
                guest_woo_without_customer_woo_id += 1


shopify_customers_with_multiple_order_woo_ids = {
    shopify_id: woo_ids
    for shopify_id, woo_ids
    in shopify_customer_to_order_woo_ids.items()
    if len(woo_ids) > 1
}


print("CUSTOMER IDENTITY AUDIT")
print("=" * 70)

print()
print("DATABASE")
print("-" * 70)

print(
    "Customers:",
    total_customers,
)

print(
    "Customers with Woo ID:",
    customers_with_woo_id,
)

print(
    "Orders:",
    total_orders,
)

print(
    "Qualifying orders:",
    qualifying_orders,
)


print()
print("ORDER SOURCES")
print("-" * 70)

for source, count in sorted(
    source_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{source!r}: {count}"
    )


print()
print("QUALIFYING ORDER SOURCES")
print("-" * 70)

for source, count in sorted(
    qualifying_source_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{source!r}: {count}"
    )


print()
print("QUALIFYING CUSTOMER COVERAGE")
print("-" * 70)

print(
    "With Shopify customer:",
    qualifying_with_shopify_customer,
)

print(
    "Without Shopify customer:",
    qualifying_without_shopify_customer,
)


print()
print("WOOCOMMERCE REGISTERED CUSTOMER LINKS")
print("-" * 70)

print(
    "Order/customer Woo ID matches:",
    registered_woo_matches,
)

print(
    "Order/customer Woo ID mismatches:",
    registered_woo_mismatches,
)


print()
print("WOOCOMMERCE GUEST ORDERS")
print("-" * 70)

print(
    "Guest order attached to customer "
    "with Woo ID:",
    guest_woo_with_customer_woo_id,
)

print(
    "Guest order without customer Woo ID:",
    guest_woo_without_customer_woo_id,
)


print()
print("IDENTITY CONFLICTS")
print("-" * 70)

print(
    "Woo IDs mapped to multiple "
    "Shopify customers:",
    len(
        woo_ids_with_multiple_shopify_customers
    ),
)

print(
    "Shopify customers associated with "
    "multiple registered Woo IDs:",
    len(
        shopify_customers_with_multiple_order_woo_ids
    ),
)


if mismatch_examples:
    print()
    print("REGISTERED LINK MISMATCH EXAMPLES")
    print("-" * 70)

    for (
        order_name,
        reporting_order_at,
        order_woo_id,
        customer_woo_id,
        shopify_customer_id,
    ) in mismatch_examples:
        print(
            order_name,
            "|",
            reporting_order_at,
            "| order Woo:",
            order_woo_id,
            "| customer Woo:",
            customer_woo_id,
            "| Shopify:",
            shopify_customer_id,
        )


if missing_customer_examples:
    print()
    print("QUALIFYING ORDERS WITHOUT CUSTOMER")
    print("-" * 70)

    for (
        order_name,
        reporting_order_at,
        source_system,
        woo_customer_id,
    ) in missing_customer_examples:
        print(
            order_name,
            "|",
            reporting_order_at,
            "| source:",
            source_system,
            "| Woo:",
            woo_customer_id,
        )


if woo_ids_with_multiple_shopify_customers:
    print()
    print("WOO ID -> MULTIPLE SHOPIFY CUSTOMERS")
    print("-" * 70)

    for woo_id, shopify_ids in list(
        sorted(
            woo_ids_with_multiple_shopify_customers.items()
        )
    )[:20]:
        print(
            woo_id,
            "->",
            sorted(shopify_ids),
        )


if shopify_customers_with_multiple_order_woo_ids:
    print()
    print("SHOPIFY CUSTOMER -> MULTIPLE WOO IDS")
    print("-" * 70)

    for shopify_id, woo_ids in list(
        sorted(
            shopify_customers_with_multiple_order_woo_ids.items()
        )
    )[:20]:
        print(
            shopify_id,
            "->",
            sorted(woo_ids),
        )