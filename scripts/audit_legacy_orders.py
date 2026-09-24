from datetime import datetime

from superspeciosa_analytics.shopify import graphql


QUERY = """
query AuditLegacyOrders(
  $first: Int!
  $search: String!
) {
  orders(
    first: $first
    query: $search
    sortKey: PROCESSED_AT
  ) {
    nodes {
      id
      name

      createdAt
      processedAt
      updatedAt

      sourceName
      sourceIdentifier

      test
      cancelledAt
      displayFinancialStatus
      currencyCode

      subtotalPriceSet {
        shopMoney {
          amount
        }
      }

      totalShippingPriceSet {
        shopMoney {
          amount
        }
      }

      totalTaxSet {
        shopMoney {
          amount
        }
      }

      totalPriceSet {
        shopMoney {
          amount
        }
      }

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

      wooOrderNumber: metafield(
        namespace: "woo"
        key: "_order_number"
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
  }
}
"""


SAMPLES = [
    (
        "2021",
        "processed_at:>='2021-01-01T00:00:00Z' "
        "processed_at:<'2022-01-01T00:00:00Z'",
    ),
    (
        "2022",
        "processed_at:>='2022-01-01T00:00:00Z' "
        "processed_at:<'2023-01-01T00:00:00Z'",
    ),
    (
        "2023",
        "processed_at:>='2023-01-01T00:00:00Z' "
        "processed_at:<'2024-01-01T00:00:00Z'",
    ),
    (
        "Jan-Jun 2024",
        "processed_at:>='2024-01-01T00:00:00Z' "
        "processed_at:<'2024-07-01T00:00:00Z'",
    ),
    (
        "August 2024",
        "processed_at:>='2024-08-01T00:00:00Z' "
        "processed_at:<'2024-09-01T00:00:00Z'",
    ),
    (
        "September 1-10 2024",
        "processed_at:>='2024-09-01T00:00:00Z' "
        "processed_at:<'2024-09-11T00:00:00Z'",
    ),
    (
        "September 11-20 2024",
        "processed_at:>='2024-09-11T00:00:00Z' "
        "processed_at:<'2024-09-21T00:00:00Z'",
    ),
    (
        "September 21-30 2024",
        "processed_at:>='2024-09-21T00:00:00Z' "
        "processed_at:<'2024-10-01T00:00:00Z'",
    ),
    (
        "October 1-5 2024",
        "processed_at:>='2024-10-01T00:00:00Z' "
        "processed_at:<'2024-10-06T00:00:00Z'",
    ),
]


def metafield_value(value):
    if value is None:
        return None

    return value["value"]


def parse_datetime(value):
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def print_order(order):
    created = parse_datetime(order["createdAt"])
    processed = parse_datetime(order["processedAt"])

    migration_gap = created - processed

    customer = order["customer"]

    print(f"Order: {order['name']}")
    print(f"Shopify ID: {order['id']}")

    print(f"createdAt:   {order['createdAt']}")
    print(f"processedAt: {order['processedAt']}")
    print(
        "created - processed:",
        migration_gap,
    )

    print(f"sourceName: {order['sourceName']!r}")
    print(
        "sourceIdentifier:",
        repr(order["sourceIdentifier"]),
    )

    print(
        "Woo order ID:",
        metafield_value(order["wooOrderId"]),
    )

    print(
        "Woo order number:",
        metafield_value(order["wooOrderNumber"]),
    )

    print(
        "Woo customer ID on order:",
        metafield_value(order["wooCustomerId"]),
    )

    print(
        "Shopify customer ID:",
        customer["id"] if customer else None,
    )

    print(
        "Woo customer ID on customer:",
        (
            metafield_value(
                customer["wooCustomerId"]
            )
            if customer
            else None
        ),
    )

    print(
        "Financial status:",
        order["displayFinancialStatus"],
    )

    print(
        "Cancelled:",
        order["cancelledAt"] is not None,
    )

    print(
        "Test:",
        order["test"],
    )

    print(
        "Subtotal:",
        order["subtotalPriceSet"]["shopMoney"]["amount"],
    )

    print(
        "Shipping:",
        order["totalShippingPriceSet"]["shopMoney"]["amount"],
    )

    print(
        "Tax:",
        order["totalTaxSet"]["shopMoney"]["amount"],
    )

    print(
        "Total:",
        order["totalPriceSet"]["shopMoney"]["amount"],
    )


for label, search in SAMPLES:
    data = graphql(
        QUERY,
        variables={
            "first": 5,
            "search": search,
        },
    )

    orders = data["orders"]["nodes"]

    print()
    print("=" * 80)
    print(label)
    print(f"Sample size: {len(orders)}")
    print("=" * 80)

    for order in orders:
        print()
        print_order(order)