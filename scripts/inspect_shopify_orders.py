from superspeciosa_analytics.shopify import graphql


QUERY = """
query {
  orders(
    first: 10
    sortKey: PROCESSED_AT
    reverse: true
  ) {
    nodes {
      id
      name
      processedAt
      updatedAt
      cancelledAt
      test
      displayFinancialStatus
      currencyCode
      taxesIncluded

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

      originalTotalAdditionalFeesSet {
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

      totalRefundedSet {
        shopMoney {
          amount
          currencyCode
        }
      }

      customer {
        id
      }

      transactions {
        id
        kind
        status
        test

        amountSet {
          shopMoney {
            amount
            currencyCode
          }
        }
      }

      refunds(first: 10) {
        id
        createdAt

        totalRefundedSet {
          shopMoney {
            amount
            currencyCode
          }
        }
      }

      lineItems(first: 50) {
        nodes {
            id
            title
            quantity

            product {
            id
            }

            variant {
            id
            }

            originalTotalSet {
            shopMoney {
                amount
                currencyCode
            }
            }

            discountAllocations {
            allocatedAmountSet {
                shopMoney {
                amount
                currencyCode
                }
            }
            }
        }
    }
  }
}
"""


def money(value):
    if value is None:
        return None

    return value["shopMoney"]["amount"]


data = graphql(QUERY)

orders = data["orders"]["nodes"]

for order in orders:
    successful_payment = any(
        transaction["status"] == "SUCCESS"
        and transaction["kind"] in {"SALE", "CAPTURE"}
        for transaction in order["transactions"]
    )

    print()
    print("=" * 60)
    print(f"Order: {order['name']}")
    print(f"Processed: {order['processedAt']}")
    print(f"Financial status: {order['displayFinancialStatus']}")
    print(f"Successful payment: {successful_payment}")
    print(f"Test: {order['test']}")
    print(f"Cancelled: {order['cancelledAt'] is not None}")
    print(f"Taxes included: {order['taxesIncluded']}")
    print(f"Subtotal: {money(order['subtotalPriceSet'])}")
    print(f"Shipping: {money(order['totalShippingPriceSet'])}")
    print(f"Tax: {money(order['totalTaxSet'])}")
    print(
        "Additional fees:",
        money(order["originalTotalAdditionalFeesSet"]),
    )
    print(f"Total charged: {money(order['totalPriceSet'])}")
    print(f"Total refunded: {money(order['totalRefundedSet'])}")
    print(f"Customer ID present: {order['customer'] is not None}")
    print(f"Refund records: {len(order['refunds'])}")
    print(f"Line items: {len(order['lineItems']['nodes'])}")