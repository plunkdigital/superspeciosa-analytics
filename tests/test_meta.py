import pytest

from superspeciosa_analytics.meta import (
    MetaConfigurationError,
    ad_account_path,
    get_ad_account_id,
)


def test_ad_account_id_removes_act_prefix(
    monkeypatch,
):
    monkeypatch.setenv(
        "META_AD_ACCOUNT_ID",
        "act_123456789",
    )

    assert (
        get_ad_account_id()
        == "123456789"
    )


def test_ad_account_path(
    monkeypatch,
):
    monkeypatch.setenv(
        "META_AD_ACCOUNT_ID",
        "123456789",
    )

    assert (
        ad_account_path()
        == "act_123456789"
    )

    assert (
        ad_account_path(
            "insights"
        )
        == "act_123456789/insights"
    )


def test_missing_ad_account_id_raises(
    monkeypatch,
):
    monkeypatch.delenv(
        "META_AD_ACCOUNT_ID",
        raising=False,
    )

    with pytest.raises(
        MetaConfigurationError,
        match="META_AD_ACCOUNT_ID",
    ):
        get_ad_account_id()