import os
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


class MetaConfigurationError(RuntimeError):
    pass


class MetaAPIError(RuntimeError):
    pass


def get_access_token() -> str:
    value = os.getenv(
        "META_ACCESS_TOKEN",
        "",
    ).strip()

    if not value:
        raise MetaConfigurationError(
            "META_ACCESS_TOKEN is not configured."
        )

    return value


def get_ad_account_id() -> str:
    value = os.getenv(
        "META_AD_ACCOUNT_ID",
        "",
    ).strip()

    if not value:
        raise MetaConfigurationError(
            "META_AD_ACCOUNT_ID is not configured."
        )

    return value.removeprefix("act_")


def get_api_version() -> str:
    value = os.getenv(
        "META_API_VERSION",
        "",
    ).strip()

    if not value:
        raise MetaConfigurationError(
            "META_API_VERSION is not configured."
        )

    return value


def get_base_url() -> str:
    return (
        "https://graph.facebook.com/"
        f"{get_api_version()}"
    )


def ad_account_path(
    suffix: str = "",
) -> str:
    base = (
        f"act_{get_ad_account_id()}"
    )

    if suffix:
        return (
            f"{base}/{suffix.lstrip('/')}"
        )

    return base


def get(
    path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_params = dict(
        params or {}
    )

    request_params[
        "access_token"
    ] = get_access_token()

    response = httpx.get(
        (
            f"{get_base_url()}/"
            f"{path.lstrip('/')}"
        ),
        params=request_params,
        timeout=30,
    )

    if not response.is_success:
        raise MetaAPIError(
            "Meta API request failed. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    payload = response.json()

    if "error" in payload:
        raise MetaAPIError(
            str(payload["error"])
        )

    return payload