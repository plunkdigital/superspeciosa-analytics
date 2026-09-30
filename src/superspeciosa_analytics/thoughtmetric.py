import os
from datetime import date

import httpx
from dotenv import load_dotenv


load_dotenv()


class ThoughtMetricConfigurationError(
    RuntimeError
):
    pass


class ThoughtMetricAPIError(
    RuntimeError
):
    pass


def get_api_key() -> str:
    value = os.getenv(
        "THOUGHTMETRIC_API_KEY"
    )

    if not value:
        raise ThoughtMetricConfigurationError(
            "THOUGHTMETRIC_API_KEY "
            "is not configured."
        )

    return value


def get_project_id() -> str:
    value = os.getenv(
        "THOUGHTMETRIC_PROJECT_ID"
    )

    if not value:
        raise ThoughtMetricConfigurationError(
            "THOUGHTMETRIC_PROJECT_ID "
            "is not configured."
        )

    return value


def get_base_url() -> str:
    return os.getenv(
        "THOUGHTMETRIC_BASE_URL",
        "https://thoughtmetric.io/api/v1",
    ).rstrip("/")


def get(
    path: str,
    *,
    params: dict[str, str],
) -> dict:
    request_params = {
        "projectId": get_project_id(),
        **params,
    }

    response = httpx.get(
        f"{get_base_url()}{path}",
        headers={
            "Authorization": (
                f"Bearer {get_api_key()}"
            ),
        },
        params=request_params,
        timeout=60.0,
    )

    if not response.is_success:
        raise ThoughtMetricAPIError(
            f"ThoughtMetric GET {path} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    return response.json()


def get_channel_performance(
    *,
    start: date,
    end: date,
) -> dict:
    """
    ThoughtMetric dates are inclusive.

    No model parameter is supplied so the API
    uses the attribution model configured on
    the ThoughtMetric project.
    """
    if start > end:
        raise ValueError(
            "Start date must not be after end date."
        )

    return get(
        "/performance_data_by_channel",
        params={
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "interval": "day",
        },
    )