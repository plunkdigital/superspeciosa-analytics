from superspeciosa_analytics.slack_app import (
    _normalize_request,
)


def test_normalize_plain_slack_request():
    assert (
        _normalize_request(
            "  DAILY "
        )
        == "daily"
    )


def test_normalize_app_mention():
    assert (
        _normalize_request(
            "<@U123ABC456> freshness"
        )
        == "freshness"
    )