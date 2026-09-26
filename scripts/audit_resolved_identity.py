from collections import Counter, defaultdict
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Customer, Order


ZERO = Decimal("0")


def is_qualifying(order: Order) -> bool:
    return (
        order.has_successful_payment
        and not order.is_test
        and order.cancelled_at is None
        and order.product_revenue > ZERO
    )


def resolve_identity(
    order: Order,
    customer: Customer | None,
) -> tuple[str | None, str]:
    """
    Return:
        (canonical identity key, resolution method)
    """

    # For original WooCommerce orders, the customer ID stored
    # on the original order is the strongest source evidence.
    if (
        order.source_system == "woocommerce"
        and order.woo_customer_id is not None
        and order.woo_customer_id != "0"
    ):
        return (
            f"woo:{order.woo_customer_id}",
            "woo_order",
        )

    # For guest Woo orders and native Shopify orders, use the
    # migrated Woo identity attached to the Shopify customer
    # when one exists.
    if (
        customer is not None
        and customer.woo_customer_id is not None
        and customer.woo_customer_id != "0"
    ):
        return (
            f"woo:{customer.woo_customer_id}",
            "woo_customer",
        )

    # Otherwise Shopify Customer ID is the stable identity.
    if customer is not None:
        return (
            f"shopify:{customer.shopify_customer_id}",
            "shopify_customer",
        )

    return None, "unresolved"


with SessionLocal() as session:
    rows = session.execute(
        select(
            Order,
            Customer,
        )
        .outerjoin(
            Customer,
            Order.customer_id == Customer.id,
        )
        .order_by(
            Order.reporting_order_at,
            Order.id,
        )
        .execution_options(
            yield_per=5000
        )
    )

    method_counts = Counter()

    qualifying_orders = 0
    resolved_orders = 0
    unresolved_orders = []

    identity_orders = defaultdict(int)
    identity_first_order = {}

    for order, customer in rows:
        if not is_qualifying(order):
            continue

        qualifying_orders += 1

        identity_key, method = resolve_identity(
            order,
            customer,
        )

        method_counts[method] += 1

        if identity_key is None:
            if len(unresolved_orders) < 50:
                unresolved_orders.append(
                    (
                        order.shopify_order_name,
                        order.reporting_order_at,
                        order.source_system,
                        order.woo_customer_id,
                    )
                )

            continue

        resolved_orders += 1
        identity_orders[identity_key] += 1

        if identity_key not in identity_first_order:
            identity_first_order[
                identity_key
            ] = (
                order.shopify_order_name,
                order.reporting_order_at,
            )


unique_identities = len(
    identity_orders
)


repeat_identities = sum(
    1
    for count in identity_orders.values()
    if count > 1
)


single_order_identities = sum(
    1
    for count in identity_orders.values()
    if count == 1
)


print("RESOLVED CUSTOMER IDENTITY AUDIT")
print("=" * 70)

print()
print("QUALIFYING ORDERS")
print("-" * 70)

print(
    "Qualifying orders:",
    qualifying_orders,
)

print(
    "Resolved:",
    resolved_orders,
)

print(
    "Unresolved:",
    qualifying_orders - resolved_orders,
)


print()
print("RESOLUTION METHODS")
print("-" * 70)

for method, count in sorted(
    method_counts.items()
):
    print(
        f"{method}: {count}"
    )


print()
print("CUSTOMER IDENTITIES")
print("-" * 70)

print(
    "Unique resolved identities:",
    unique_identities,
)

print(
    "One qualifying order:",
    single_order_identities,
)

print(
    "More than one qualifying order:",
    repeat_identities,
)


print()
print("ORDER DEPTH")
print("-" * 70)

depth_buckets = Counter()

for count in identity_orders.values():
    if count == 1:
        depth_buckets["1"] += 1
    elif count <= 3:
        depth_buckets["2-3"] += 1
    elif count <= 10:
        depth_buckets["4-10"] += 1
    elif count <= 25:
        depth_buckets["11-25"] += 1
    else:
        depth_buckets["26+"] += 1

for bucket in [
    "1",
    "2-3",
    "4-10",
    "11-25",
    "26+",
]:
    print(
        f"{bucket}:",
        depth_buckets[bucket],
    )


if unresolved_orders:
    print()
    print("UNRESOLVED QUALIFYING ORDERS")
    print("-" * 70)

    for (
        order_name,
        reporting_order_at,
        source_system,
        woo_customer_id,
    ) in unresolved_orders:
        print(
            order_name,
            "|",
            reporting_order_at,
            "| source:",
            source_system,
            "| Woo:",
            woo_customer_id,
        )