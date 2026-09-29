import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class EverflowConfigurationError(RuntimeError):
    pass


class EverflowAPIError(RuntimeError):
    pass


def get_api_key() -> str:
    value = os.getenv(
        "EVERFLOW_API_KEY"
    )

    if not value:
        raise EverflowConfigurationError(
            "EVERFLOW_API_KEY is not configured."
        )

    return value


def get_base_url() -> str:
    return os.getenv(
        "EVERFLOW_BASE_URL",
        "https://api.eflow.team/v1",
    ).rstrip("/")


def get_currency() -> str:
    return os.getenv(
        "EVERFLOW_CURRENCY",
        "USD",
    )


def get_timezone_id() -> int | None:
    value = os.getenv(
        "EVERFLOW_TIMEZONE_ID"
    )

    if not value:
        return None

    return int(value)


def _headers() -> dict[str, str]:
    return {
        "X-Eflow-Api-Key": get_api_key(),
        "Content-Type": "application/json",
    }


def get(
    path: str,
) -> dict:
    response = httpx.get(
        f"{get_base_url()}{path}",
        headers=_headers(),
        timeout=30.0,
    )

    if not response.is_success:
        raise EverflowAPIError(
            f"Everflow GET {path} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


def post(
    path: str,
    payload: dict,
) -> dict:
    response = httpx.post(
        f"{get_base_url()}{path}",
        headers=_headers(),
        json=payload,
        timeout=60.0,
    )

    if not response.is_success:
        raise EverflowAPIError(
            f"Everflow POST {path} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()