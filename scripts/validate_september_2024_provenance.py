from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order


START = datetime(
    2024,
    9,
    1,
    tzinfo=UTC,
)

END = datetime(
    2024,
    10,
    1,
    tzinfo=UTC,
)


with SessionLocal() as session:
    orders = session.scalars(
        select(Order)
        .where(Order.processed_at >= START)
        .where(Order.processed_at < END)
        .options(
            selectinload(Order.customer)
        )
        .order_by(Order.processed_at)
    ).all()


print(f"September 2024 orders: {len(orders)}")
print()


source_name_counts = Counter(
    order.source_name
    for order in orders
)

source_system_counts = Counter(
    order.source_system
    for order in orders
)


print("SOURCE NAME COUNTS")
print("-" * 60)

for source_name, count in sorted(
    source_name_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{source_name!r}: {count}"
    )


print()
print("SOURCE SYSTEM COUNTS")
print("-" * 60)

for source_system, count in sorted(
    source_system_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{source_system!r}: {count}"
    )


failures = []


reporting_date_mismatches = [
    order
    for order in orders
    if order.reporting_order_at
    != order.processed_at
]

if reporting_date_mismatches:
    failures.append(
        f"{len(reporting_date_mismatches)} orders "
        "have reporting_order_at != processed_at"
    )


matrixify_orders = [
    order
    for order in orders
    if order.source_name == "Matrixify App"
]


woocommerce_orders = [
    order
    for order in orders
    if order.source_system == "woocommerce"
]


matrixify_unknown_orders = [
    order
    for order in orders
    if order.source_system == "matrixify_unknown"
]


shopify_orders = [
    order
    for order in orders
    if order.source_system == "shopify"
]


bad_woocommerce = [
    order
    for order in matrixify_orders
    if (
        order.source_order_id is not None
        and order.source_system != "woocommerce"
    )
]

if bad_woocommerce:
    failures.append(
        f"{len(bad_woocommerce)} Matrixify orders "
        "with Woo order IDs are not classified "
        "as woocommerce"
    )


bad_matrixify_unknown = [
    order
    for order in matrixify_orders
    if (
        order.source_order_id is None
        and order.source_system
        != "matrixify_unknown"
    )
]

if bad_matrixify_unknown:
    failures.append(
        f"{len(bad_matrixify_unknown)} Matrixify orders "
        "without Woo order IDs are not classified "
        "as matrixify_unknown"
    )


bad_non_matrixify = [
    order
    for order in orders
    if (
        order.source_name != "Matrixify App"
        and order.source_system != "shopify"
    )
]

if bad_non_matrixify:
    failures.append(
        f"{len(bad_non_matrixify)} non-Matrixify "
        "orders are not classified as shopify"
    )


woocommerce_missing_source_id = [
    order
    for order in woocommerce_orders
    if order.source_order_id is None
]

if woocommerce_missing_source_id:
    failures.append(
        f"{len(woocommerce_missing_source_id)} "
        "WooCommerce orders have no source_order_id"
    )


bad_shopify_source_ids = [
    order
    for order in shopify_orders
    if order.source_order_id
    != order.shopify_order_id
]

if bad_shopify_source_ids:
    failures.append(
        f"{len(bad_shopify_source_ids)} Shopify "
        "orders have an unexpected source_order_id"
    )


woo_source_ids = [
    order.source_order_id
    for order in woocommerce_orders
    if order.source_order_id is not None
]

woo_source_id_counts = Counter(
    woo_source_ids
)

duplicate_woo_source_ids = {
    source_id: count
    for source_id, count
    in woo_source_id_counts.items()
    if count > 1
}

if duplicate_woo_source_ids:
    failures.append(
        f"{len(duplicate_woo_source_ids)} duplicate "
        "WooCommerce source order IDs found"
    )


registered_matches = 0
registered_mismatches = []
guest_with_customer_woo_id = 0
guest_without_customer_woo_id = 0

for order in woocommerce_orders:
    order_woo_customer_id = (
        order.woo_customer_id
    )

    customer_woo_id = (
        order.customer.woo_customer_id
        if order.customer
        else None
    )

    if (
        order_woo_customer_id is not None
        and order_woo_customer_id != "0"
    ):
        if (
            order_woo_customer_id
            == customer_woo_id
        ):
            registered_matches += 1
        else:
            registered_mismatches.append(
                (
                    order.shopify_order_name,
                    order_woo_customer_id,
                    customer_woo_id,
                )
            )

    elif order_woo_customer_id == "0":
        if customer_woo_id is not None:
            guest_with_customer_woo_id += 1
        else:
            guest_without_customer_woo_id += 1


print()
print("PROVENANCE")
print("-" * 60)

print(
    "Matrixify orders:",
    len(matrixify_orders),
)

print(
    "WooCommerce orders:",
    len(woocommerce_orders),
)

print(
    "Matrixify unknown:",
    len(matrixify_unknown_orders),
)

print(
    "Shopify-era orders:",
    len(shopify_orders),
)


print()
print("CUSTOMER LINKAGE")
print("-" * 60)

print(
    "Registered Woo customer matches:",
    registered_matches,
)

print(
    "Registered Woo customer mismatches:",
    len(registered_mismatches),
)

print(
    "Guest orders attached to customer "
    "with Woo ID:",
    guest_with_customer_woo_id,
)

print(
    "Guest orders without Woo customer ID:",
    guest_without_customer_woo_id,
)


print()
print("DATA QUALITY")
print("-" * 60)

print(
    "Reporting date mismatches:",
    len(reporting_date_mismatches),
)

print(
    "Duplicate Woo order IDs:",
    len(duplicate_woo_source_ids),
)


if registered_mismatches:
    print()
    print("CUSTOMER MISMATCH EXAMPLES")
    print("-" * 60)

    for (
        order_name,
        order_woo_id,
        customer_woo_id,
    ) in registered_mismatches[:20]:
        print(
            order_name,
            "order Woo customer:",
            order_woo_id,
            "attached customer Woo ID:",
            customer_woo_id,
        )


if duplicate_woo_source_ids:
    print()
    print("DUPLICATE WOO ORDER IDS")
    print("-" * 60)

    for source_id, count in list(
        duplicate_woo_source_ids.items()
    )[:20]:
        print(
            source_id,
            count,
        )


print()

if failures:
    print("PROVENANCE VALIDATION FAILED")
    print()

    for failure in failures:
        print(f"- {failure}")

    raise SystemExit(1)


print("Provenance validation passed.")