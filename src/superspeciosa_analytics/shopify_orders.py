from typing import Any

from superspeciosa_analytics.shopify import graphql


RECENT_ORDERS_QUERY = """
query RecentOrders($first: Int!) {
  orders(
    first: $first
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


def fetch_recent_orders(
    limit: int = 10,
) -> list[dict[str, Any]]:
    data = graphql(
        RECENT_ORDERS_QUERY,
        variables={"first": limit},
    )

    return data["orders"]["nodes"]