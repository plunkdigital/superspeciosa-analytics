import json

from sqlalchemy import select

from superspeciosa_analytics.appstle import (
    get_customer_contract,
    get_past_orders,
)
from superspeciosa_analytics.database import (
    SessionLocal,
)
from superspeciosa_analytics.models import (
    Order,
)
from superspeciosa_analytics.shopify import (
    graphql,
)


ORDER_APPSTLE_QUERY = """
query OrderAppstleDetails($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Order {
      id
      name

      metafield(
        namespace: "appstle_subscription"
        key: "details"
      ) {
        type
        value
      }
    }
  }
}
"""


def numeric_gid(
    value,
) -> str | None:
    if value is None:
        return None

    value = str(value)

    if not value:
        return None

    return value.rsplit(
        "/",
        1,
    )[-1]


def first_value(
    value,
    keys: set[str],
):
    if isinstance(
        value,
        dict,
    ):
        for key, item in value.items():
            if (
                key in keys
                and item is not None
            ):
                return item

        for item in value.values():
            result = first_value(
                item,
                keys,
            )

            if result is not None:
                return result

    elif isinstance(
        value,
        list,
    ):
        for item in value:
            result = first_value(
                item,
                keys,
            )

            if result is not None:
                return result

    return None


with SessionLocal() as session:
    candidate_orders = session.scalars(
        select(
            Order
        )
        .where(
            Order.source_name.ilike(
                "%subscription%"
            )
        )
        .order_by(
            Order.reporting_order_at.desc()
        )
        .limit(10)
    ).all()


if not candidate_orders:
    raise RuntimeError(
        "No recent subscription-source "
        "Shopify orders found."
    )


shopify_ids = [
    order.shopify_order_id
    for order in candidate_orders
]


data = graphql(
    ORDER_APPSTLE_QUERY,
    variables={
        "ids": shopify_ids,
    },
)


nodes = [
    node
    for node in data["nodes"]
    if node is not None
]


linked_contracts = []


print()
print("SHOPIFY / APPSTLE LINK CHECK")
print("=" * 72)


for node in nodes:
    metafield = node.get(
        "metafield"
    )

    if not metafield:
        continue

    raw_value = metafield.get(
        "value"
    )

    if not raw_value:
        continue

    details = json.loads(
        raw_value
    )

    customer = (
        details.get(
            "customer",
            {},
        )
        or {}
    )

    contract = (
        details.get(
            "subscriptionContract",
            {},
        )
        or {}
    )

    first_order = (
        details.get(
            "firstOrder",
            {},
        )
        or {}
    )

    contract_gid = contract.get(
        "id"
    )

    if not contract_gid:
        continue

    contract_id = numeric_gid(
        contract_gid
    )

    linked_contracts.append(
        (
            contract_id,
            str(
                customer.get(
                    "id"
                )
            ).rsplit(
                "/",
                1,
            )[-1],
        )
    )

    print()
    print("-" * 72)

    print(
        "Shopify order:",
        node.get("name"),
    )

    print(
        "Shopify order ID:",
        node.get("id"),
    )

    print(
        "Shopify customer ID:",
        customer.get("id"),
    )

    print(
        "Contract ID:",
        contract_gid,
    )

    print(
        "Contract status:",
        contract.get(
            "status"
        ),
    )

    print(
        "Current cycle:",
        contract.get(
            "currentCycle"
        ),
    )

    print(
        "First order ID:",
        first_order.get(
            "id"
        ),
    )

    print(
        "First order date:",
        first_order.get(
            "createdAt"
        ),
    )


if not linked_contracts:
    raise RuntimeError(
        "No Appstle contract links found "
        "in recent subscription orders."
    )


(
    probe_contract_id,
    probe_customer_id,
) = linked_contracts[0]


print()
print("=" * 72)
print("APPSTLE CONTRACT API CHECK")
print("-" * 72)

print(
    "Contract ID:",
    probe_contract_id,
)


contract_details = get_customer_contract(
    customer_id=probe_customer_id,
    contract_id=probe_contract_id,
)

print(
    "Customer ID:",
    probe_customer_id,
)

print(
    "Contract ID:",
    probe_contract_id,
)

print(
    "Returned contract ID:",
    contract_details.get(
        "subscriptionContractId"
    ),
)

print(
    "Status:",
    contract_details.get(
        "status"
    ),
)

print(
    "Created at:",
    contract_details.get(
        "createdAt"
    ),
)

print(
    "Updated at:",
    contract_details.get(
        "updatedAt"
    ),
)

print(
    "Next billing date:",
    contract_details.get(
        "nextBillingDate"
    ),
)

print(
    "Successful orders:",
    contract_details.get(
        "totalSuccessfulOrders"
    ),
)

print(
    "Billing frequency:",
    contract_details.get(
        "billingPolicyIntervalCount"
    ),
    contract_details.get(
        "billingPolicyInterval"
    ),
)


past_orders = get_past_orders(
    probe_contract_id
)


print()
print("APPSTLE PAST ORDERS CHECK")
print("-" * 72)

print(
    "Response type:",
    type(past_orders).__name__,
)


if isinstance(
    past_orders,
    list,
):
    print(
        "Rows:",
        len(past_orders),
    )

    for index, row in enumerate(
        past_orders[:3],
        start=1,
    ):
        print()
        print(
            f"Past order row {index}"
        )

        print(
            "Keys:",
            sorted(
                row.keys()
            ),
        )

        for key in (
            "id",
            "contractId",
            "billingAttemptId",
            "billingDate",
            "attemptTime",
            "status",
            "graphOrderId",
            "orderId",
            "orderName",
            "orderAmount",
            "orderAmountUSD",
        ):
            if key in row:
                print(
                    f"{key}:",
                    row.get(key),
                )


print()
print(
    "Subscription linkage check passed."
)