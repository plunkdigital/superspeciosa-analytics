import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class AppstleConfigurationError(
    RuntimeError
):
    pass


class AppstleAPIError(
    RuntimeError
):
    pass


def get_api_key() -> str:
    value = os.getenv(
        "APPSTLE_API_KEY"
    )

    if not value:
        raise AppstleConfigurationError(
            "APPSTLE_API_KEY is not configured."
        )

    return value


def get_base_url() -> str:
    return os.getenv(
        "APPSTLE_BASE_URL",
        (
            "https://subscription-admin.appstle.com"
            "/api/external/v2"
        ),
    ).rstrip("/")


def get(
    path: str,
    *,
    params: dict | None = None,
):
    response = httpx.get(
        f"{get_base_url()}{path}",
        headers={
            "X-API-Key": get_api_key(),
        },
        params=params,
        timeout=60.0,
    )

    if not response.is_success:
        raise AppstleAPIError(
            f"Appstle GET {path} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response


def get_contract_details(
    contract_id: str,
) -> dict:
    response = get(
        "/subscription-contract-details",
        params={
            "contractId": contract_id,
        },
    )

    data = response.json()

    if not isinstance(
        data,
        list,
    ):
        raise AppstleAPIError(
            "Expected Appstle contract details "
            "to return a list."
        )

    expected = str(
        contract_id
    )

    for row in data:
        candidate = row.get(
            "subscriptionContractId"
        )

        if (
            candidate is not None
            and str(candidate) == expected
        ):
            return row

        graph_id = row.get(
            "graphSubscriptionContractId"
        )

        if graph_id:
            numeric_graph_id = str(
                graph_id
            ).rsplit(
                "/",
                1,
            )[-1]

            if (
                numeric_graph_id
                == expected
            ):
                return row

    raise AppstleAPIError(
        "Appstle did not return requested "
        f"contract {contract_id}."
    )

def get_customer_subscriptions(
    customer_id: str,
) -> list[dict]:
    response = get(
        f"/subscription-customers/{customer_id}"
    )

    data = response.json()

    if isinstance(
        data,
        list,
    ):
        return data

    if not isinstance(
        data,
        dict,
    ):
        raise AppstleAPIError(
            "Unexpected Appstle customer "
            "subscriptions response type."
        )

    contracts = data.get(
        "subscriptionContracts"
    )

    if isinstance(
        contracts,
        dict,
    ):
        nodes = contracts.get(
            "nodes"
        )

        if isinstance(
            nodes,
            list,
        ):
            return nodes

    raise AppstleAPIError(
        "Appstle customer response did not "
        "contain subscriptionContracts.nodes."
    )


def get_customer_contract(
    *,
    customer_id: str,
    contract_id: str,
) -> dict:
    subscriptions = (
        get_customer_subscriptions(
            customer_id
        )
    )

    expected = str(
        contract_id
    )

    for row in subscriptions:
        candidates = (
            row.get(
                "subscriptionContractId"
            ),
            row.get(
                "id"
            ),
            row.get(
                "graphSubscriptionContractId"
            ),
        )

        for candidate in candidates:
            if candidate is None:
                continue

            candidate_value = str(
                candidate
            ).rsplit(
                "/",
                1,
            )[-1]

            if candidate_value == expected:
                return row

    raise AppstleAPIError(
        "Appstle customer subscriptions "
        f"did not contain contract {contract_id}."
    )

def get_past_orders(
    contract_id: str,
):
    response = get(
        "/subscription-billing-attempts/past-orders",
        params={
            "contractId": contract_id,
        },
    )

    return response.json()