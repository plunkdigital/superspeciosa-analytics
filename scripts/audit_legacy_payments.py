from superspeciosa_analytics.shopify import graphql


QUERY = """
query AuditLegacyPayments(
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
      processedAt
      createdAt
      sourceName

      displayFinancialStatus
      cancelledAt
      test

      paymentGatewayNames

      subtotalPriceSet {
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

      transactions {
        id
        kind
        status
        gateway
        test

        amountSet {
          shopMoney {
            amount
            currencyCode
          }
        }
      }

      refunds {
        id
        createdAt

        totalRefundedSet {
          shopMoney {
            amount
            currencyCode
          }
        }
      }

      wooTransactionId: metafield(
        namespace: "woo"
        key: "transaction_id"
      ) {
        value
      }

      wooPaymentMethod: metafield(
        namespace: "woo"
        key: "payment_method"
      ) {
        value
      }

      wooCaptured: metafield(
        namespace: "woo"
        key: "_nmi_charge_captured"
      ) {
        value
      }
    }
  }
}
"""


SAMPLES = [
    (
        "2021",
        "processed_at:>='2021-01-01T00:00:00Z' "
        "processed_at:<'2021-02-01T00:00:00Z'",
    ),
    (
        "2022",
        "processed_at:>='2022-01-01T00:00:00Z' "
        "processed_at:<'2022-02-01T00:00:00Z'",
    ),
    (
        "2023",
        "processed_at:>='2023-01-01T00:00:00Z' "
        "processed_at:<'2023-02-01T00:00:00Z'",
    ),
    (
        "Early 2024",
        "processed_at:>='2024-01-01T00:00:00Z' "
        "processed_at:<'2024-02-01T00:00:00Z'",
    ),
    (
        "September 2024",
        "processed_at:>='2024-09-01T00:00:00Z' "
        "processed_at:<'2024-09-25T00:00:00Z'",
    ),
]


def value(field):
    if field is None:
        return None

    return field["value"]


for label, search in SAMPLES:
    data = graphql(
        QUERY,
        variables={
            "first": 50,
            "search": search,
        },
    )

    matrixify_orders = [
        order
        for order in data["orders"]["nodes"]
        if order["sourceName"] == "Matrixify App"
    ][:5]

    print()
    print("=" * 80)
    print(label)
    print(
        f"Matrixify sample size: "
        f"{len(matrixify_orders)}"
    )
    print("=" * 80)

    for order in matrixify_orders:
        print()
        print(f"Order: {order['name']}")
        print(f"Processed: {order['processedAt']}")
        print(
            "Financial status:",
            order["displayFinancialStatus"],
        )
        print(
            "Cancelled:",
            order["cancelledAt"] is not None,
        )

        print(
            "Subtotal:",
            order["subtotalPriceSet"][
                "shopMoney"
            ]["amount"],
        )

        print(
            "Total:",
            order["totalPriceSet"][
                "shopMoney"
            ]["amount"],
        )

        print(
            "Payment gateways:",
            order["paymentGatewayNames"],
        )

        print(
            "Woo transaction ID:",
            value(order["wooTransactionId"]),
        )

        print(
            "Woo payment method:",
            value(order["wooPaymentMethod"]),
        )

        print(
            "Woo captured:",
            value(order["wooCaptured"]),
        )

        print("Transactions:")

        if not order["transactions"]:
            print("  NONE")

        for transaction in order["transactions"]:
            print(
                " ",
                transaction["kind"],
                transaction["status"],
                transaction["gateway"],
                transaction["amountSet"][
                    "shopMoney"
                ]["amount"],
            )

        print(
            "Refund records:",
            len(order["refunds"]),
        )