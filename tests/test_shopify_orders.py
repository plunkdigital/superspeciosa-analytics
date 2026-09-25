from datetime import UTC, datetime
from unittest.mock import patch

from superspeciosa_analytics.shopify_orders import (
    fetch_orders_by_processed_range,
)


def test_processed_range_excludes_exact_end_boundary():
    start = datetime(
        2022,
        9,
        1,
        tzinfo=UTC,
    )

    end = datetime(
        2022,
        10,
        1,
        tzinfo=UTC,
    )

    response = {
        "orders": {
            "nodes": [
                {
                    "id": "inside",
                    "processedAt": (
                        "2022-09-30T23:59:59Z"
                    ),
                    "lineItems": {
                        "nodes": [],
                        "pageInfo": {
                            "hasNextPage": False,
                        },
                    },
                },
                {
                    "id": "boundary",
                    "processedAt": (
                        "2022-10-01T00:00:00Z"
                    ),
                    "lineItems": {
                        "nodes": [],
                        "pageInfo": {
                            "hasNextPage": False,
                        },
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "endCursor": None,
            },
        }
    }

    with patch(
        "superspeciosa_analytics."
        "shopify_orders.graphql",
        return_value=response,
    ):
        orders = fetch_orders_by_processed_range(
            start=start,
            end=end,
        )

    assert [
        order["id"]
        for order in orders
    ] == ["inside"]

def test_large_order_line_items_are_refetched():
    start = datetime(
        2023,
        3,
        1,
        tzinfo=UTC,
    )

    end = datetime(
        2023,
        4,
        1,
        tzinfo=UTC,
    )

    initial_response = {
        "orders": {
            "nodes": [
                {
                    "id": "large-order",
                    "name": "287821",
                    "processedAt": (
                        "2023-03-10T23:30:21Z"
                    ),
                    "lineItems": {
                        "nodes": [
                            {"id": f"line-{i}"}
                            for i in range(50)
                        ],
                        "pageInfo": {
                            "hasNextPage": True,
                        },
                    },
                }
            ],
            "pageInfo": {
                "hasNextPage": False,
                "endCursor": None,
            },
        }
    }

    detailed_response = {
        "order": {
            "id": "large-order",
            "name": "287821",
            "lineItems": {
                "nodes": [
                    {"id": f"line-{i}"}
                    for i in range(66)
                ],
                "pageInfo": {
                    "hasNextPage": False,
                },
            },
        }
    }

    with patch(
        "superspeciosa_analytics."
        "shopify_orders.graphql",
        side_effect=[
            initial_response,
            detailed_response,
        ],
    ) as mocked_graphql:
        orders = (
            fetch_orders_by_processed_range(
                start=start,
                end=end,
            )
        )

    assert len(orders) == 1

    assert (
        len(
            orders[0][
                "lineItems"
            ]["nodes"]
        )
        == 66
    )

    assert mocked_graphql.call_count == 2