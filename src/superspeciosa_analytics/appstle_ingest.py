import json

from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)
from decimal import Decimal

from sqlalchemy import select

from superspeciosa_analytics.appstle import (
    get_customer_subscriptions,
    get_past_orders,
)
from superspeciosa_analytics.models import (
    AppstleSubscriptionContract,
    AppstleSubscriptionOrder,
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

      metafield(
        namespace: "appstle_subscription"
        key: "details"
      ) {
        value
      }
    }
  }
}
"""


@dataclass
class DiscoveredContract:
    contract_id: str
    shopify_customer_id: str
    shopify_customer_gid: str

    explicit_origin_shopify_order_id: (
        str | None
    )

    explicit_origin_order_at: (
        datetime | None
    )


def numeric_id(
    value,
) -> str | None:
    if value is None:
        return None

    value = str(
        value
    ).strip()

    if not value:
        return None

    return value.rsplit(
        "/",
        1,
    )[-1]


def order_gid(
    value,
) -> str | None:
    value = numeric_id(
        value
    )

    if not value:
        return None

    return (
        "gid://shopify/Order/"
        f"{value}"
    )


def customer_gid(
    value,
) -> str | None:
    value = numeric_id(
        value
    )

    if not value:
        return None

    return (
        "gid://shopify/Customer/"
        f"{value}"
    )


def parse_datetime(
    value,
) -> datetime | None:
    if not value:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    return datetime.fromisoformat(
        str(value).replace(
            "Z",
            "+00:00",
        )
    )


def decimal_value(
    value,
) -> Decimal | None:
    if value is None:
        return None

    return Decimal(
        str(value)
    )


def _chunks(
    values: list,
    size: int,
):
    for position in range(
        0,
        len(values),
        size,
    ):
        yield values[
            position:
            position + size
        ]


def discover_contracts(
    session,
    *,
    shopify_batch_size: int = 50,
    contract_limit: int | None = None,
) -> tuple[
    dict[str, DiscoveredContract],
    int,
]:
    shopify_order_ids = list(
        session.scalars(
            select(
                Order.shopify_order_id
            )
            .where(
                Order.shopify_order_id.is_not(
                    None
                )
            )
            .where(
                Order.source_name.ilike(
                    "%subscription%"
                )
            )
            .order_by(
                Order.reporting_order_at.desc()
            )
        )
    )

    contracts: dict[
        str,
        DiscoveredContract,
    ] = {}

    for batch_number, batch in enumerate(
        _chunks(
            shopify_order_ids,
            shopify_batch_size,
        ),
        start=1,
    ):
        print(
            f"Scanning Shopify batch "
            f"{batch_number} "
            f"({len(batch)} orders)..."
        )
        data = graphql(
            ORDER_APPSTLE_QUERY,
            variables={
                "ids": batch,
            },
        )

        for node in data.get(
            "nodes",
            [],
        ):
            if not node:
                continue

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

            contract = (
                details.get(
                    "subscriptionContract"
                )
                or {}
            )

            customer = (
                details.get(
                    "customer"
                )
                or {}
            )

            first_order = (
                details.get(
                    "firstOrder"
                )
                or {}
            )

            contract_id = numeric_id(
                contract.get(
                    "id"
                )
            )

            shopify_customer_id = (
                numeric_id(
                    customer.get(
                        "id"
                    )
                )
            )

            if (
                not contract_id
                or not shopify_customer_id
            ):
                continue

            explicit_origin = order_gid(
                first_order.get(
                    "id"
                )
            )

            explicit_origin_at = (
                parse_datetime(
                    first_order.get(
                        "createdAt"
                    )
                )
            )

            existing = contracts.get(
                contract_id
            )

            if existing:
                if (
                    existing.shopify_customer_id
                    != shopify_customer_id
                ):
                    raise RuntimeError(
                        "Contract "
                        f"{contract_id} "
                        "was observed with multiple "
                        "Shopify customers."
                    )

                if (
                    explicit_origin
                    and
                    existing
                    .explicit_origin_shopify_order_id
                    and
                    explicit_origin
                    != existing
                    .explicit_origin_shopify_order_id
                ):
                    raise RuntimeError(
                        "Contract "
                        f"{contract_id} "
                        "was observed with multiple "
                        "explicit origin orders."
                    )

                if (
                    not existing
                    .explicit_origin_shopify_order_id
                    and explicit_origin
                ):
                    existing.explicit_origin_shopify_order_id = (
                        explicit_origin
                    )

                    existing.explicit_origin_order_at = (
                        explicit_origin_at
                    )

                continue

            contracts[
                contract_id
            ] = DiscoveredContract(
                contract_id=contract_id,
                shopify_customer_id=(
                    shopify_customer_id
                ),
                shopify_customer_gid=(
                    customer_gid(
                        shopify_customer_id
                    )
                ),
                explicit_origin_shopify_order_id=(
                    explicit_origin
                ),
                explicit_origin_order_at=(
                    explicit_origin_at
                ),
            )
            if (
                contract_limit is not None
                and len(contracts)
                >= contract_limit
            ):
                print(
                    "Reached discovery limit: "
                    f"{len(contracts)} contracts"
                )

                return (
                    contracts,
                    len(
                        shopify_order_ids
                    ),
                )

        if (
            contract_limit is not None
            and len(contracts)
            >= contract_limit
        ):
            print(
                "Reached discovery limit: "
                f"{len(contracts)} contracts"
            )

            return (
                contracts,
                len(
                    shopify_order_ids
                ),
            )

    print(
        "Unique contracts discovered: "
        f"{len(contracts)}"
    )


def find_contract(
    rows: list[dict],
    contract_id: str,
) -> dict | None:
    expected = str(
        contract_id
    )

    for row in rows:
        for key in (
            "id",
            "subscriptionContractId",
            "graphSubscriptionContractId",
        ):
            candidate = numeric_id(
                row.get(
                    key
                )
            )

            if (
                candidate
                == expected
            ):
                return row

    return None


def earliest_success_order(
    rows: list[dict],
) -> dict | None:
    successful = [
        row
        for row in rows
        if str(
            row.get(
                "status",
                ""
            )
        ).upper() == "SUCCESS"
        and (
            row.get(
                "graphOrderId"
            )
            or row.get(
                "orderId"
            )
        )
    ]

    def event_time(
        row: dict,
    ):
        return (
            parse_datetime(
                row.get(
                    "orderProcessedAt"
                )
            )
            or parse_datetime(
                row.get(
                    "attemptTime"
                )
            )
            or parse_datetime(
                row.get(
                    "billingDate"
                )
            )
            or datetime.max.replace(
                tzinfo=timezone.utc
            )
        )

    if not successful:
        return None

    return min(
        successful,
        key=event_time,
    )

def subscription_order_source_key(
    row: dict,
) -> str:
    appstle_row_id = row.get(
        "id"
    )

    if appstle_row_id is not None:
        return (
            f"id:{appstle_row_id}"
        )

    contract_id = numeric_id(
        row.get(
            "contractId"
        )
    )

    shopify_order_id = numeric_id(
        row.get(
            "graphOrderId"
        )
        or row.get(
            "orderId"
        )
    )

    if (
        contract_id
        and shopify_order_id
    ):
        return (
            "contract_order:"
            f"{contract_id}:"
            f"{shopify_order_id}"
        )

    raise RuntimeError(
        "Appstle past-order row has "
        "neither an id nor a usable "
        "contract/order natural key."
    )

def upsert_subscription_order(
    session,
    *,
    row: dict,
    now: datetime,
):
    source_key = (
        subscription_order_source_key(
            row
        )
    )

    record = session.scalar(
        select(
            AppstleSubscriptionOrder
        ).where(
            AppstleSubscriptionOrder
            .source_key
            == source_key
        )
    )

    if record is None:
        record = (
            AppstleSubscriptionOrder(
                source_key=source_key,
            )
        )

        session.add(
            record
        )

    appstle_row_id = row.get(
        "id"
    )

    record.appstle_row_id = (
        int(appstle_row_id)
        if appstle_row_id is not None
        else None
    )

    record.contract_id = str(
        row.get(
            "contractId"
        )
    )

    record.billing_attempt_id = (
        row.get(
            "billingAttemptId"
        )
    )

    record.billing_date = (
        parse_datetime(
            row.get(
                "billingDate"
            )
        )
    )

    record.attempt_time = (
        parse_datetime(
            row.get(
                "attemptTime"
            )
        )
    )

    record.status = (
        row.get(
            "status"
        )
    )

    record.shopify_order_id = (
        order_gid(
            row.get(
                "graphOrderId"
            )
            or row.get(
                "orderId"
            )
        )
    )

    record.shopify_order_name = (
        row.get(
            "orderName"
        )
    )

    record.order_amount = (
        decimal_value(
            row.get(
                "orderAmount"
            )
        )
    )

    record.order_amount_usd = (
        decimal_value(
            row.get(
                "orderAmountUSD"
            )
        )
    )

    record.order_processed_at = (
        parse_datetime(
            row.get(
                "orderProcessedAt"
            )
        )
    )

    record.ingested_at = now

    return True


def import_appstle(
    session,
    *,
    limit: int | None = None,
    shopify_batch_size: int = 50,
) -> dict:
    now = datetime.now(
        timezone.utc
    )

    (
        contracts,
        subscription_source_orders,
    ) = discover_contracts(
        session,
        shopify_batch_size=(
            shopify_batch_size
        ),
        contract_limit=limit,
    )   

    contract_list = sorted(
        contracts.values(),
        key=lambda value: (
            value.contract_id
        ),
    )

    if limit is not None:
        contract_list = (
            contract_list[
                :limit
            ]
        )

    customer_cache: dict[
        str,
        list[dict],
    ] = {}

    imported_contracts = 0
    past_order_rows = 0
    past_order_rows_imported = 0
    past_order_rows_missing_id = 0
    success_order_rows = 0
    explicit_origins = 0
    inferred_origins = 0
    missing_contract_state = 0

    linked_order_ids: set[
        str
    ] = set()

    for contract_number, discovered in enumerate(
        contract_list,
        start=1,
    ):
        print(
            "Importing Appstle contract "
            f"{contract_number}/"
            f"{len(contract_list)}: "
            f"{discovered.contract_id}"
        )
        customer_rows = (
            customer_cache.get(
                discovered
                .shopify_customer_id
            )
        )

        if customer_rows is None:
            customer_rows = (
                get_customer_subscriptions(
                    discovered
                    .shopify_customer_id
                )
            )

            customer_cache[
                discovered
                .shopify_customer_id
            ] = customer_rows

        current = find_contract(
            customer_rows,
            discovered.contract_id,
        )

        if current is None:
            missing_contract_state += 1

            print(
                "Current Appstle state not found "
                "for contract "
                f"{discovered.contract_id}; "
                "preserving historical contract."
            )

            current = {}

        past_orders = get_past_orders(
            discovered.contract_id
        )

        successful_origin = (
            earliest_success_order(
                past_orders
            )
        )

        if (
            discovered
            .explicit_origin_shopify_order_id
        ):
            origin_order_id = (
                discovered
                .explicit_origin_shopify_order_id
            )

            origin_order_at = (
                discovered
                .explicit_origin_order_at
            )

            origin_link_method = (
                "explicit_metafield"
            )

            explicit_origins += 1

        elif successful_origin:
            origin_order_id = order_gid(
                successful_origin.get(
                    "graphOrderId"
                )
                or successful_origin.get(
                    "orderId"
                )
            )

            origin_order_at = (
                parse_datetime(
                    successful_origin.get(
                        "orderProcessedAt"
                    )
                )
                or parse_datetime(
                    successful_origin.get(
                        "attemptTime"
                    )
                )
                or parse_datetime(
                    successful_origin.get(
                        "billingDate"
                    )
                )
            )

            origin_link_method = (
                "past_orders_earliest"
            )

            inferred_origins += 1

        else:
            origin_order_id = None
            origin_order_at = None
            origin_link_method = None

        record = session.scalar(
            select(
                AppstleSubscriptionContract
            ).where(
                AppstleSubscriptionContract
                .contract_id
                == discovered.contract_id
            )
        )

        if record is None:
            record = (
                AppstleSubscriptionContract(
                    contract_id=(
                        discovered
                        .contract_id
                    ),
                    first_seen_at=now,
                )
            )

            session.add(
                record
            )

        record.shopify_customer_id = (
            discovered
            .shopify_customer_id
        )

        record.shopify_customer_gid = (
            discovered
            .shopify_customer_gid
        )

        record.status = (
            current.get(
                "status"
            )
        )

        record.created_at = (
            parse_datetime(
                current.get(
                    "createdAt"
                )
            )
        )

        record.next_billing_date = (
            parse_datetime(
                current.get(
                    "nextBillingDate"
                )
            )
        )

        record.origin_shopify_order_id = (
            origin_order_id
        )

        record.origin_order_at = (
            origin_order_at
        )

        record.origin_link_method = (
            origin_link_method
        )

        record.last_seen_at = now
        record.ingested_at = now

        imported_contracts += 1

        for row in past_orders:
            past_order_rows += 1

            if str(
                row.get(
                    "status",
                    ""
                )
            ).upper() == "SUCCESS":
                success_order_rows += 1

            shopify_order_id = (
                order_gid(
                    row.get(
                        "graphOrderId"
                    )
                    or row.get(
                        "orderId"
                    )
                )
            )

            if shopify_order_id:
                linked_order_ids.add(
                    shopify_order_id
                )

            upsert_subscription_order(
                session,
                row=row,
                now=now,
            )

            past_order_rows_imported += 1

    session.flush()

    existing_shopify_ids: set[
        str
    ] = set()

    for batch in _chunks(
        list(
            linked_order_ids
        ),
        500,
    ):
        existing_shopify_ids.update(
            session.scalars(
                select(
                    Order.shopify_order_id
                ).where(
                    Order.shopify_order_id.in_(
                        batch
                    )
                )
            )
        )

    return {
        "subscription_source_orders": (
            subscription_source_orders
        ),
        "unique_contracts_discovered": (
            len(
                contracts
            )
        ),
        "contracts_attempted": (
            len(
                contract_list
            )
        ),
        "contracts_imported": (
            imported_contracts
        ),
        "missing_contract_state": (
            missing_contract_state
        ),
        "past_order_rows": (
            past_order_rows
        ),
        "success_order_rows": (
            success_order_rows
        ),
        "shopify_order_links_found": (
            len(
                existing_shopify_ids
            )
        ),
        "shopify_order_links_missing": (
            len(
                linked_order_ids
                - existing_shopify_ids
            )
        ),
        "explicit_origins": (
            explicit_origins
        ),
        "inferred_origins": (
            inferred_origins
        ),
        "past_order_rows_imported": (
            past_order_rows_imported
        ),
        "past_order_rows_missing_id": (
            past_order_rows_missing_id
        ),
    }