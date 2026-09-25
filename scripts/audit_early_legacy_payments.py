from collections import Counter
from decimal import Decimal

from superspeciosa_analytics.shopify import graphql


QUERY = """
query EarlyLegacyPayments(
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
      processedAt
      sourceName

      displayFinancialStatus
      cancelledAt
      test

      subtotalPriceSet {
        shopMoney {
          amount
        }
      }

      transactions {
        kind
        status
        gateway

        amountSet {
          shopMoney {
            amount
          }
        }
      }

      wooOrderId: metafield(
        namespace: "woo"
        key: "id_"
      ) {
        value
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

    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


SEARCH = (
    "processed_at:>='2016-07-14T00:00:00Z' "
    "processed_at:<'2016-09-01T00:00:00Z'"
)


def value(field):
    if field is None:
        return None

    return field["value"]


def has_successful_payment(order):
    return any(
        transaction["status"] == "SUCCESS"
        and transaction["kind"] in {
            "SALE",
            "CAPTURE",
        }
        for transaction in order["transactions"]
    )


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


matrixify_orders = [
    order
    for order in orders
    if order["sourceName"] == "Matrixify App"
]


status_counts = Counter(
    order["displayFinancialStatus"]
    for order in matrixify_orders
)


successful_payment_count = sum(
    has_successful_payment(order)
    for order in matrixify_orders
)


no_successful_payment = [
    order
    for order in matrixify_orders
    if not has_successful_payment(order)
]


positive_uncancelled_without_payment = [
    order
    for order in no_successful_payment
    if (
        Decimal(
            order["subtotalPriceSet"][
                "shopMoney"
            ]["amount"]
        ) > 0
        and order["cancelledAt"] is None
        and not order["test"]
    )
]


problem_status_counts = Counter(
    order["displayFinancialStatus"]
    for order
    in positive_uncancelled_without_payment
)


print(
    "Period: 2016-07-14 through 2016-08-31"
)

print(
    "Matrixify orders:",
    len(matrixify_orders),
)

print()

print("FINANCIAL STATUS")
print("-" * 60)

for status, count in sorted(
    status_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{status!r}: {count}"
    )


print()
print("PAYMENT EVIDENCE")
print("-" * 60)

print(
    "Successful SALE/CAPTURE:",
    successful_payment_count,
)

print(
    "No successful SALE/CAPTURE:",
    len(no_successful_payment),
)

print(
    "Positive, non-cancelled orders "
    "without successful payment:",
    len(
        positive_uncancelled_without_payment
    ),
)


print()
print(
    "STATUS OF POSITIVE NON-CANCELLED "
    "ORDERS WITHOUT PAYMENT"
)
print("-" * 60)

for status, count in sorted(
    problem_status_counts.items(),
    key=lambda item: str(item[0]),
):
    print(
        f"{status!r}: {count}"
    )


print()
print("SAMPLE")
print("-" * 60)

for order in (
    positive_uncancelled_without_payment[:20]
):
    print()

    print(
        f"{order['name']} | "
        f"{order['processedAt']}"
    )

    print(
        "  Financial status:",
        order["displayFinancialStatus"],
    )

    print(
        "  Subtotal:",
        order["subtotalPriceSet"][
            "shopMoney"
        ]["amount"],
    )

    print(
        "  Woo order ID:",
        value(order["wooOrderId"]),
    )

    print(
        "  Woo transaction ID:",
        value(order["wooTransactionId"]),
    )

    print(
        "  Woo payment method:",
        value(order["wooPaymentMethod"]),
    )

    print(
        "  Woo captured:",
        value(order["wooCaptured"]),
    )

    print(
        "  Shopify transactions:",
        [
            (
                transaction["kind"],
                transaction["status"],
                transaction["gateway"],
            )
            for transaction
            in order["transactions"]
        ],
    )