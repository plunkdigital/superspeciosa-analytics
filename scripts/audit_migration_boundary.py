from collections import Counter
from datetime import datetime

from superspeciosa_analytics.shopify import graphql


QUERY = """
query MigrationBoundary(
  $first: Int!
  $after: String
  $search: String!
) {
  orders(
    first: $first
    after: $after
    query: $search
    sortKey: PROCESSED_AT
  ) {
    nodes {
      id
      name
      createdAt
      processedAt
      sourceName
      sourceIdentifier

      wooOrderId: metafield(
        namespace: "woo"
        key: "id_"
      ) {
        value
      }

      wooCustomerId: metafield(
        namespace: "woo"
        key: "customer_id"
      ) {
        value
      }

      customer {
        id

        wooCustomerId: metafield(
          namespace: "woo"
          key: "id_"
        ) {
          value
        }
      }
    }

    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


SEARCH = (
    "processed_at:>='2024-09-01T00:00:00Z' "
    "processed_at:<'2024-10-01T00:00:00Z'"
)


def metafield_value(field):
    if field is None:
        return None

    return field["value"]


orders = []
cursor = None

while True:
    data = graphql(
        QUERY,
        variables={
            "first": 250,
            "after": cursor,
            "search": SEARCH,
        },
    )

    connection = data["orders"]

    orders.extend(connection["nodes"])

    if not connection["pageInfo"]["hasNextPage"]:
        break

    cursor = connection["pageInfo"]["endCursor"]


orders.sort(
    key=lambda order: order["processedAt"]
)


source_counts = Counter(
    order["sourceName"]
    for order in orders
)


matrixify_orders = [
    order
    for order in orders
    if order["sourceName"] == "Matrixify App"
]


web_orders = [
    order
    for order in orders
    if order["sourceName"] == "web"
]


print(f"September orders: {len(orders)}")

print()
print("SOURCE COUNTS")
print("-" * 60)

for source, count in sorted(
    source_counts.items(),
    key=lambda item: str(item[0]),
):
    print(f"{source!r}: {count}")


if matrixify_orders:
    last_matrixify = max(
        matrixify_orders,
        key=lambda order: order["processedAt"],
    )

    print()
    print("LAST MATRIXIFY ORDER")
    print("-" * 60)
    print(f"Order: {last_matrixify['name']}")
    print(
        f"Processed: "
        f"{last_matrixify['processedAt']}"
    )
    print(
        f"Created: "
        f"{last_matrixify['createdAt']}"
    )
    print(
        "Woo order ID:",
        metafield_value(
            last_matrixify["wooOrderId"]
        ),
    )


if web_orders:
    first_web = min(
        web_orders,
        key=lambda order: order["processedAt"],
    )

    print()
    print("FIRST WEB ORDER")
    print("-" * 60)
    print(f"Order: {first_web['name']}")
    print(
        f"Processed: "
        f"{first_web['processedAt']}"
    )
    print(
        f"Created: "
        f"{first_web['createdAt']}"
    )
    print(
        f"Source identifier: "
        f"{first_web['sourceIdentifier']!r}"
    )


if matrixify_orders and web_orders:
    last_matrixify_time = datetime.fromisoformat(
        last_matrixify[
            "processedAt"
        ].replace("Z", "+00:00")
    )

    first_web_time = datetime.fromisoformat(
        first_web[
            "processedAt"
        ].replace("Z", "+00:00")
    )

    print()
    print("TRANSITION")
    print("-" * 60)

    print(
        "Time between last Matrixify "
        "and first web order:",
        first_web_time - last_matrixify_time,
    )

    overlapping_matrixify = [
        order
        for order in matrixify_orders
        if order["processedAt"]
        > first_web["processedAt"]
    ]

    early_web = [
        order
        for order in web_orders
        if order["processedAt"]
        < last_matrixify["processedAt"]
    ]

    print(
        "Matrixify orders after first web order:",
        len(overlapping_matrixify),
    )

    print(
        "Web orders before last Matrixify order:",
        len(early_web),
    )


registered_match = 0
registered_mismatch = []
guest_with_link = 0
guest_without_link = 0

for order in matrixify_orders:
    order_customer_id = metafield_value(
        order["wooCustomerId"]
    )

    customer = order["customer"]

    customer_woo_id = (
        metafield_value(
            customer["wooCustomerId"]
        )
        if customer
        else None
    )

    if (
        order_customer_id is not None
        and order_customer_id != "0"
    ):
        if order_customer_id == customer_woo_id:
            registered_match += 1
        else:
            registered_mismatch.append(
                {
                    "order": order["name"],
                    "order_woo_customer": (
                        order_customer_id
                    ),
                    "customer_woo_id": (
                        customer_woo_id
                    ),
                }
            )

    elif order_customer_id == "0":
        if customer_woo_id is not None:
            guest_with_link += 1
        else:
            guest_without_link += 1


print()
print("MATRIXIFY CUSTOMER LINK AUDIT")
print("-" * 60)

print(
    "Registered orders with matching "
    "Woo customer IDs:",
    registered_match,
)

print(
    "Registered orders with mismatched "
    "or missing customer Woo ID:",
    len(registered_mismatch),
)

print(
    "Guest orders attached to a customer "
    "with Woo ID:",
    guest_with_link,
)

print(
    "Guest orders without a Woo customer link:",
    guest_without_link,
)


if registered_mismatch:
    print()
    print("REGISTERED CUSTOMER MISMATCH EXAMPLES")
    print("-" * 60)

    for mismatch in registered_mismatch[:20]:
        print(
            mismatch["order"],
            "order Woo customer:",
            mismatch["order_woo_customer"],
            "attached customer Woo ID:",
            mismatch["customer_woo_id"],
        )