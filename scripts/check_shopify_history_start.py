from superspeciosa_analytics.shopify import graphql


QUERY = """
query {
  orders(
    first: 10
    sortKey: PROCESSED_AT
    reverse: false
  ) {
    nodes {
      id
      name
      createdAt
      processedAt
      sourceName
      sourceIdentifier

      test
      cancelledAt
      displayFinancialStatus

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

      subtotalPriceSet {
        shopMoney {
          amount
          currencyCode
        }
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


def value(field):
    if field is None:
        return None

    return field["value"]


data = graphql(QUERY)

orders = data["orders"]["nodes"]

print(f"Oldest orders returned: {len(orders)}")
print()

for order in orders:
    customer = order["customer"]

    print("=" * 70)

    print(f"Order: {order['name']}")
    print(f"Shopify ID: {order['id']}")

    print(f"Processed: {order['processedAt']}")
    print(f"Created:   {order['createdAt']}")

    print(f"Source: {order['sourceName']!r}")
    print(
        "Source identifier:",
        repr(order["sourceIdentifier"]),
    )

    print(
        "Woo order ID:",
        value(order["wooOrderId"]),
    )

    print(
        "Woo customer ID on order:",
        value(order["wooCustomerId"]),
    )

    print(
        "Shopify customer ID:",
        customer["id"] if customer else None,
    )

    print(
        "Woo customer ID on customer:",
        (
            value(customer["wooCustomerId"])
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
        order["subtotalPriceSet"][
            "shopMoney"
        ]["amount"],
    )

    print()