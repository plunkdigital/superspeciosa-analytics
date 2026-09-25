from superspeciosa_analytics.shopify import graphql


QUERY = """
query InspectLargeOrder($search: String!) {
  orders(
    first: 5
    query: $search
  ) {
    nodes {
      id
      name
      processedAt

      lineItems(first: 250) {
        nodes {
          id
          title
          quantity
        }

        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""


data = graphql(
    QUERY,
    variables={
        "search": "name:287821",
    },
)

orders = data["orders"]["nodes"]

if not orders:
    raise SystemExit("Order 287821 not found.")

for order in orders:
    print(f"Order: {order['name']}")
    print(f"Shopify ID: {order['id']}")
    print(f"Processed: {order['processedAt']}")

    line_items = order["lineItems"]

    print(
        "Line item records returned:",
        len(line_items["nodes"]),
    )

    print(
        "Has more than 250:",
        line_items["pageInfo"]["hasNextPage"],
    )

    print(
        "Total quantity:",
        sum(
            item["quantity"]
            for item in line_items["nodes"]
        ),
    )

    print()