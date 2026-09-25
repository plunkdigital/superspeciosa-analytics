import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


SHOPIFY_SHOP = os.environ[
    "SHOPIFY_SHOP"
].removesuffix(".myshopify.com")

SHOPIFY_CLIENT_ID = os.environ[
    "SHOPIFY_CLIENT_ID"
]

SHOPIFY_CLIENT_SECRET = os.environ[
    "SHOPIFY_CLIENT_SECRET"
]

SHOPIFY_API_VERSION = os.getenv(
    "SHOPIFY_API_VERSION",
    "2026-07",
)


_access_token: str | None = None
_access_token_expires_at: float = 0.0


def get_access_token() -> str:
    global _access_token
    global _access_token_expires_at

    now = time.monotonic()

    if (
        _access_token is not None
        and now < _access_token_expires_at
    ):
        return _access_token

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

    if not response.is_success:
        raise RuntimeError(
            "Shopify access-token request failed. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    payload = response.json()

    _access_token = payload["access_token"]

    expires_in = int(
        payload.get(
            "expires_in",
            86399,
        )
    )

    # Refresh five minutes before Shopify's
    # reported expiry.
    refresh_buffer = 300

    _access_token_expires_at = (
        time.monotonic()
        + max(
            expires_in - refresh_buffer,
            60,
        )
    )

    return _access_token


def graphql(
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    access_token = get_access_token()

    response = httpx.post(
        (
            f"https://{SHOPIFY_SHOP}.myshopify.com"
            f"/admin/api/{SHOPIFY_API_VERSION}"
            "/graphql.json"
        ),
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": (
                access_token
            ),
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
        raise RuntimeError(
            payload["errors"]
        )

    return payload["data"]