import os
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


SHOPIFY_SHOP = os.environ["SHOPIFY_SHOP"].removesuffix(".myshopify.com")
SHOPIFY_CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
SHOPIFY_CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
SHOPIFY_API_VERSION = os.getenv(
    "SHOPIFY_API_VERSION",
    "2026-07",
)


def get_access_token() -> str:
    response = httpx.post(
        (
            f"https://{SHOPIFY_SHOP}.myshopify.com"
            "/admin/oauth/access_token"
        ),
        data={
            "grant_type": "client_credentials",
            "client_id": SHOPIFY_CLIENT_ID,
            "client_secret": SHOPIFY_CLIENT_SECRET,
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    return payload["access_token"]


def graphql(
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    access_token = get_access_token()

    response = httpx.post(
        (
            f"https://{SHOPIFY_SHOP}.myshopify.com"
            f"/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        ),
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        },
        json={
            "query": query,
            "variables": variables or {},
        },
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]