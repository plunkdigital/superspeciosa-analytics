from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.database import SessionLocal
from superspeciosa_analytics.models import Order
from superspeciosa_analytics.shopify import graphql


QUERY = """
query ReconcileOrder($id: ID!) {
  order(id: $id) {
    id
    name
    processedAt
    cancelledAt
    test
    displayFinancialStatus
    currencyCode
    taxesIncluded

    subtotalPriceSet {
      shopMoney {
        amount
      }
    }

    totalShippingPriceSet {
      shopMoney {
        amount
      }
    }

    totalTaxSet {
      shopMoney {
        amount
      }
    }

    originalTotalAdditionalFeesSet {
      shopMoney {
        amount
      }
    }

    totalPriceSet {
      shopMoney {
        amount
      }
    }

    customer {
      id
    }

    transactions {
      kind
      status
    }

    lineItems(first: 50) {
      nodes {
        id
      }
    }
  }
}
"""


def money(value):
    if value is None:
        return Decimal("0")

    return Decimal(
        value["shopMoney"]["amount"]
    )


def successful_payment(transactions):
    return any(
        transaction["status"] == "SUCCESS"
        and transaction["kind"] in {"SALE", "CAPTURE"}
        for transaction in transactions
    )


with SessionLocal() as session:
    orders = session.scalars(
        select(Order)
        .order_by(Order.processed_at.desc())
        .limit(10)
    ).all()

    failures = []

    total_db_revenue = Decimal("0")
    total_shopify_revenue = Decimal("0")

    total_db_shipping = Decimal("0")
    total_shopify_shipping = Decimal("0")

    total_db_tax = Decimal("0")
    total_shopify_tax = Decimal("0")

    print(f"Reconciling {len(orders)} database orders...")
    print()

    for db_order in orders:
        data = graphql(
            QUERY,
            variables={
                "id": db_order.shopify_order_id,
            },
        )

        shopify = data["order"]

        if shopify is None:
            failures.append(
                (
                    db_order.shopify_order_name,
                    "Order missing from Shopify",
                )
            )
            continue

        checks = {
            "name": (
                db_order.shopify_order_name,
                shopify["name"],
            ),
            "currency": (
                db_order.currency_code,
                shopify["currencyCode"],
            ),
            "product_revenue": (
                db_order.product_revenue,
                money(shopify["subtotalPriceSet"]),
            ),
            "shipping": (
                db_order.shipping_amount,
                money(shopify["totalShippingPriceSet"]),
            ),
            "tax": (
                db_order.tax_amount,
                money(shopify["totalTaxSet"]),
            ),
            "fees": (
                db_order.fee_amount,
                money(
                    shopify[
                        "originalTotalAdditionalFeesSet"
                    ]
                ),
            ),
            "total_charged": (
                db_order.total_charged,
                money(shopify["totalPriceSet"]),
            ),
            "successful_payment": (
                db_order.has_successful_payment,
                successful_payment(
                    shopify["transactions"]
                ),
            ),
            "test": (
                db_order.is_test,
                shopify["test"],
            ),
            "cancelled": (
                db_order.cancelled_at is not None,
                shopify["cancelledAt"] is not None,
            ),
            "financial_status": (
                db_order.display_financial_status,
                shopify["displayFinancialStatus"],
            ),
            "line_count": (
                len(db_order.lines),
                len(shopify["lineItems"]["nodes"]),
            ),
        }

        mismatches = {
            name: values
            for name, values in checks.items()
            if values[0] != values[1]
        }

        if mismatches:
            for field, values in mismatches.items():
                failures.append(
                    (
                        db_order.shopify_order_name,
                        field,
                        values[0],
                        values[1],
                    )
                )

            print(
                f"{db_order.shopify_order_name}: FAIL"
            )

        else:
            print(
                f"{db_order.shopify_order_name}: OK"
            )

        total_db_revenue += (
            db_order.product_revenue
        )
        total_shopify_revenue += money(
            shopify["subtotalPriceSet"]
        )

        total_db_shipping += (
            db_order.shipping_amount
        )
        total_shopify_shipping += money(
            shopify["totalShippingPriceSet"]
        )

        total_db_tax += db_order.tax_amount
        total_shopify_tax += money(
            shopify["totalTaxSet"]
        )

    print()
    print("Totals")
    print("-" * 50)

    print(
        "Revenue:",
        total_db_revenue,
        "(DB)",
        total_shopify_revenue,
        "(Shopify)",
    )

    print(
        "Shipping:",
        total_db_shipping,
        "(DB)",
        total_shopify_shipping,
        "(Shopify)",
    )

    print(
        "Tax:",
        total_db_tax,
        "(DB)",
        total_shopify_tax,
        "(Shopify)",
    )

    print()

    if failures:
        print("RECONCILIATION FAILED")
        print()

        for failure in failures:
            print(failure)

        raise SystemExit(1)

    print("Reconciliation passed.")