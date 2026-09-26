from superspeciosa_analytics.customer_identity import (
    CustomerIdentityMethod,
    OrderCustomerClassification,
    classify_customer_order,
    resolve_customer_identity,
)


def test_registered_woo_order_uses_order_woo_id():
    identity, method = resolve_customer_identity(
        source_system="woocommerce",
        order_woo_customer_id="57453",
        shopify_customer_id=(
            "gid://shopify/Customer/123"
        ),
        customer_woo_customer_id="37240",
    )

    assert identity == "woo:57453"
    assert method == CustomerIdentityMethod.WOO_ORDER


def test_woo_guest_can_use_customer_woo_id():
    identity, method = resolve_customer_identity(
        source_system="woocommerce",
        order_woo_customer_id="0",
        shopify_customer_id=(
            "gid://shopify/Customer/123"
        ),
        customer_woo_customer_id="2822",
    )

    assert identity == "woo:2822"
    assert method == CustomerIdentityMethod.WOO_CUSTOMER


def test_native_shopify_order_uses_migrated_woo_identity():
    identity, method = resolve_customer_identity(
        source_system="shopify",
        order_woo_customer_id=None,
        shopify_customer_id=(
            "gid://shopify/Customer/123"
        ),
        customer_woo_customer_id="2822",
    )

    assert identity == "woo:2822"
    assert method == CustomerIdentityMethod.WOO_CUSTOMER


def test_new_shopify_customer_uses_shopify_id():
    identity, method = resolve_customer_identity(
        source_system="shopify",
        order_woo_customer_id=None,
        shopify_customer_id=(
            "gid://shopify/Customer/123"
        ),
        customer_woo_customer_id=None,
    )

    assert (
        identity
        == "shopify:gid://shopify/Customer/123"
    )

    assert (
        method
        == CustomerIdentityMethod.SHOPIFY_CUSTOMER
    )


def test_missing_customer_is_unresolved():
    identity, method = resolve_customer_identity(
        source_system="woocommerce",
        order_woo_customer_id="0",
        shopify_customer_id=None,
        customer_woo_customer_id=None,
    )

    assert identity is None
    assert method == CustomerIdentityMethod.UNRESOLVED


def test_first_order_is_new():
    seen = set()

    result = classify_customer_order(
        identity_key="woo:123",
        seen_identities=seen,
    )

    assert result == OrderCustomerClassification.NEW


def test_second_order_is_returning():
    seen = {"woo:123"}

    result = classify_customer_order(
        identity_key="woo:123",
        seen_identities=seen,
    )

    assert (
        result
        == OrderCustomerClassification.RETURNING
    )


def test_unresolved_identity_stays_unresolved():
    seen = set()

    result = classify_customer_order(
        identity_key=None,
        seen_identities=seen,
    )

    assert (
        result
        == OrderCustomerClassification.UNRESOLVED
    )