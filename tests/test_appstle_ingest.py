from superspeciosa_analytics.appstle_ingest import (
    earliest_success_order,
    numeric_id,
    order_gid,
)


def test_numeric_id_normalizes_gid():
    assert numeric_id(
        "gid://shopify/Order/12345"
    ) == "12345"

    assert numeric_id(
        12345
    ) == "12345"


def test_order_gid_normalizes_id():
    assert order_gid(
        12345
    ) == (
        "gid://shopify/Order/12345"
    )

    assert order_gid(
        "gid://shopify/Order/12345"
    ) == (
        "gid://shopify/Order/12345"
    )


def test_earliest_success_order():
    rows = [
        {
            "id": 3,
            "status": "SUCCESS",
            "orderId": 300,
            "attemptTime": (
                "2026-09-01T00:00:00Z"
            ),
        },
        {
            "id": 1,
            "status": "FAILED",
            "orderId": None,
            "attemptTime": (
                "2026-07-01T00:00:00Z"
            ),
        },
        {
            "id": 2,
            "status": "SUCCESS",
            "orderId": 200,
            "attemptTime": (
                "2026-08-01T00:00:00Z"
            ),
        },
    ]

    result = earliest_success_order(
        rows
    )

    assert result["id"] == 2