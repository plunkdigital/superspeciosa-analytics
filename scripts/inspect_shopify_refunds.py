from decimal import Decimal

from superspeciosa_analytics.shopify import graphql


QUERY = """
query InspectRefundedOrders($search: String!) {
  orders(
    first: 5
    sortKey: PROCESSED_AT
    reverse: true
    query: $search
  ) {
    nodes {
      id
      name
      processedAt
      displayFinancialStatus
      taxesIncluded

      subtotalPriceSet {
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

      refunds(first: 20) {
        id
        createdAt

        totalRefundedSet {
          shopMoney {
            amount
            currencyCode
          }
        }

        refundLineItems(first: 50) {
          nodes {
            quantity

            subtotalSet {
              shopMoney {
                amount
              }
            }

            totalTaxSet {
              shopMoney {
                amount
              }
            }

            lineItem {
              id
              title
            }
          }
        }

        refundShippingLines(first: 20) {
          nodes {
            subtotalAmountSet {
              shopMoney {
                amount
              }
            }

            taxAmountSet {
              shopMoney {
                amount
              }
            }
          }
        }

        orderAdjustments(first: 20) {
          nodes {
            reason

            amountSet {
              shopMoney {
                amount
              }
            }

            taxAmountSet {
              shopMoney {
                amount
              }
            }
          }
        }
      }
    }
  }
}
"""


def amount(money_bag):
    return Decimal(money_bag["shopMoney"]["amount"])


def inspect(search):
    data = graphql(
        QUERY,
        variables={"search": search},
    )

    orders = data["orders"]["nodes"]

    print()
    print("#" * 70)
    print(f"SEARCH: {search}")
    print(f"FOUND: {len(orders)}")

    for order in orders:
        print()
        print("=" * 70)
        print(f"Order: {order['name']}")
        print(f"Processed: {order['processedAt']}")
        print(f"Status: {order['displayFinancialStatus']}")
        print(f"Taxes included: {order['taxesIncluded']}")
        print(
            "Original product revenue:",
            amount(order["subtotalPriceSet"]),
        )
        print(
            "Order total refunded:",
            amount(order["totalRefundedSet"]),
        )

        for refund in order["refunds"]:
            product_refund = sum(
                (
                    amount(item["subtotalSet"])
                    for item
                    in refund["refundLineItems"]["nodes"]
                ),
                Decimal("0"),
            )

            product_tax_refund = sum(
                (
                    amount(item["totalTaxSet"])
                    for item
                    in refund["refundLineItems"]["nodes"]
                ),
                Decimal("0"),
            )

            shipping_refund = sum(
                (
                    amount(item["subtotalAmountSet"])
                    for item
                    in refund["refundShippingLines"]["nodes"]
                ),
                Decimal("0"),
            )

            shipping_tax_refund = sum(
                (
                    amount(item["taxAmountSet"])
                    for item
                    in refund["refundShippingLines"]["nodes"]
                ),
                Decimal("0"),
            )

            adjustment_amount = sum(
                (
                    amount(item["amountSet"])
                    for item
                    in refund["orderAdjustments"]["nodes"]
                ),
                Decimal("0"),
            )

            adjustment_tax = sum(
                (
                    amount(item["taxAmountSet"])
                    for item
                    in refund["orderAdjustments"]["nodes"]
                ),
                Decimal("0"),
            )

            print()
            print(f"  Refund: {refund['id']}")
            print(f"  Created: {refund['createdAt']}")
            print(
                "  Shopify total refund:",
                amount(refund["totalRefundedSet"]),
            )
            print(
                "  Product refund:",
                product_refund,
            )
            print(
                "  Product tax refund:",
                product_tax_refund,
            )
            print(
                "  Shipping refund:",
                shipping_refund,
            )
            print(
                "  Shipping tax refund:",
                shipping_tax_refund,
            )
            print(
                "  Adjustment amount:",
                adjustment_amount,
            )
            print(
                "  Adjustment tax:",
                adjustment_tax,
            )

            if refund["orderAdjustments"]["nodes"]:
                print("  Adjustments:")
                for adjustment in refund["orderAdjustments"]["nodes"]:
                    print(
                        "   ",
                        adjustment["reason"],
                        amount(adjustment["amountSet"]),
                    )


inspect("financial_status:refunded")
inspect("financial_status:partially_refunded")