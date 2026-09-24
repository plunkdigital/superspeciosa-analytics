from superspeciosa_analytics.shopify import graphql
from superspeciosa_analytics.shopify_mapper import map_shopify_order


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

      customer {
        id
      }

      transactions {
        id
        kind
        status
        test
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
                currencyCode
              }
            }

            totalTaxSet {
              shopMoney {
                amount
                currencyCode
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
                currencyCode
              }
            }

            taxAmountSet {
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
}
"""


data = graphql(QUERY)

for order in data["orders"]["nodes"]:
    mapped = map_shopify_order(order)

    print(
        mapped.shopify_order_name,
        mapped.product_revenue,
        mapped.shipping_amount,
        mapped.tax_amount,
        mapped.has_successful_payment,
        len(mapped.lines),
        len(mapped.refunds),
    )