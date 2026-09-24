from datetime import UTC, datetime
from typing import Any

from superspeciosa_analytics.shopify import graphql


ORDERS_QUERY = """
query Orders(
  $first: Int!
  $after: String
  $search: String
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
      createdAt
      processedAt
      updatedAt
      cancelledAt
      test
      displayFinancialStatus
      currencyCode
      taxesIncluded

      sourceName
      sourceIdentifier

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

        wooCustomerId: metafield(
          namespace: "woo"
          key: "id_"
        ) {
          value
        }
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

        pageInfo {
          hasNextPage
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

          pageInfo {
            hasNextPage
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

          pageInfo {
            hasNextPage
          }
        }
      }
    }

    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


def _shopify_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError(
            "Shopify range datetimes must be timezone-aware."
        )

    utc_value = value.astimezone(UTC)

    return (
        utc_value
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def fetch_recent_orders(
    limit: int = 10,
) -> list[dict[str, Any]]:
    data = graphql(
        ORDERS_QUERY,
        variables={
            "first": limit,
            "after": None,
            "search": None,
        },
    )

    return data["orders"]["nodes"]


def fetch_orders_by_processed_range(
    start: datetime,
    end: datetime,
    page_size: int = 25,
) -> list[dict[str, Any]]:
    if start >= end:
        raise ValueError(
            "Start datetime must be before end datetime."
        )

    start_value = _shopify_datetime(start)
    end_value = _shopify_datetime(end)

    search = (
        f"processed_at:>='{start_value}' "
        f"processed_at:<'{end_value}'"
    )

    orders: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        data = graphql(
            ORDERS_QUERY,
            variables={
                "first": page_size,
                "after": cursor,
                "search": search,
            },
        )

        connection = data["orders"]

        orders.extend(connection["nodes"])

        page_info = connection["pageInfo"]

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

        if cursor is None:
            raise RuntimeError(
                "Shopify reported another page "
                "without an end cursor."
            )

    return orders