from superspeciosa_analytics.shopify import graphql


QUERY = """
query InspectLegacyOrders(
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
      registeredSourceUrl

      test
      cancelledAt
      displayFinancialStatus
      currencyCode

      tags

      subtotalPriceSet {
        shopMoney {
          amount
          currencyCode
        }
      }

      totalShippingPriceSet {
        shopMoney {
          amount
          currencyCode
        }
      }

      totalTaxSet {
        shopMoney {
          amount
          currencyCode
        }
      }

      totalPriceSet {
        shopMoney {
          amount
          currencyCode
        }
      }

      customer {
        id

        metafields(first: 50) {
          nodes {
            namespace
            key
            value
            type
          }
        }
      }

      metafields(first: 50) {
        nodes {
          namespace
          key
          value
          type
        }
      }
    }
  }
}
"""


SAMPLES = [
    (
        "2023 sample",
        (
            "processed_at:>='2023-01-01T00:00:00Z' "
            "processed_at:<'2024-01-01T00:00:00Z'"
        ),
    ),
    (
        "Early 2024 sample",
        (
            "processed_at:>='2024-01-01T00:00:00Z' "
            "processed_at:<'2024-07-01T00:00:00Z'"
        ),
    ),
    (
        "August 2024 sample",
        (
            "processed_at:>='2024-08-01T00:00:00Z' "
            "processed_at:<'2024-09-01T00:00:00Z'"
        ),
    ),
    (
        "September 2024 sample",
        (
            "processed_at:>='2024-09-01T00:00:00Z' "
            "processed_at:<'2024-10-01T00:00:00Z'"
        ),
    ),
    (
        "October 2024 sample",
        (
            "processed_at:>='2024-10-01T00:00:00Z' "
            "processed_at:<'2024-11-01T00:00:00Z'"
        ),
    ),
]


def interesting_metafields(connection):
    fields = connection["nodes"]

    # Show WooCommerce / Matrixify-looking metadata first.
    interesting = [
        field
        for field in fields
        if (
            "woo" in field["namespace"].lower()
            or "woo" in field["key"].lower()
            or "matrix" in field["namespace"].lower()
            or "matrix" in field["key"].lower()
        )
    ]

    if interesting:
        return interesting

    return fields


def print_metafields(label, connection):
    fields = interesting_metafields(connection)

    if not fields:
        print(f"{label}: none")
        return

    print(f"{label}:")

    for field in fields:
        print(
            f"  {field['namespace']}.{field['key']}"
            f" = {field['value']!r}"
            f" [{field['type']}]"
        )


def inspect_sample(label, search):
    data = graphql(
        QUERY,
        variables={
            "first": 5,
            "search": search,
        },
    )

    orders = data["orders"]["nodes"]

    print()
    print("#" * 80)
    print(label)
    print(f"Found sample size: {len(orders)}")
    print("#" * 80)

    for order in orders:
        print()
        print("=" * 80)

        print(f"Order: {order['name']}")
        print(f"Shopify ID: {order['id']}")

        print()
        print("DATES")
        print(f"  createdAt:   {order['createdAt']}")
        print(f"  processedAt: {order['processedAt']}")
        print(f"  updatedAt:   {order['updatedAt']}")

        print()
        print("SOURCE")
        print(f"  sourceName:       {order['sourceName']!r}")
        print(
            f"  sourceIdentifier: "
            f"{order['sourceIdentifier']!r}"
        )
        print(
            f"  registeredSourceUrl: "
            f"{order['registeredSourceUrl']!r}"
        )

        print()
        print("ORDER STATE")
        print(f"  test: {order['test']}")
        print(
            f"  cancelled: "
            f"{order['cancelledAt'] is not None}"
        )
        print(
            f"  financial status: "
            f"{order['displayFinancialStatus']}"
        )

        print()
        print("FINANCIALS")
        print(
            "  subtotal:",
            order["subtotalPriceSet"]["shopMoney"]["amount"],
        )
        print(
            "  shipping:",
            order["totalShippingPriceSet"]["shopMoney"][
                "amount"
            ],
        )
        print(
            "  tax:",
            order["totalTaxSet"]["shopMoney"]["amount"],
        )
        print(
            "  total:",
            order["totalPriceSet"]["shopMoney"]["amount"],
        )

        print()
        print("CUSTOMER")
        print(
            "  Shopify customer ID:",
            (
                order["customer"]["id"]
                if order["customer"]
                else None
            ),
        )

        print()
        print("TAGS")
        print(
            "  ",
            ", ".join(order["tags"])
            if order["tags"]
            else "none",
        )

        print()

        print_metafields(
            "ORDER METAFIELDS",
            order["metafields"],
        )

        if order["customer"]:
            print()
            print_metafields(
                "CUSTOMER METAFIELDS",
                order["customer"]["metafields"],
            )


for sample_label, sample_search in SAMPLES:
    inspect_sample(
        sample_label,
        sample_search,
    )