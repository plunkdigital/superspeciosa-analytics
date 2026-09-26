from enum import StrEnum


class CustomerIdentityMethod(StrEnum):
    WOO_ORDER = "woo_order"
    WOO_CUSTOMER = "woo_customer"
    SHOPIFY_CUSTOMER = "shopify_customer"
    UNRESOLVED = "unresolved"


class OrderCustomerClassification(StrEnum):
    NEW = "new"
    RETURNING = "returning"
    UNRESOLVED = "unresolved"


def resolve_customer_identity(
    *,
    source_system: str | None,
    order_woo_customer_id: str | None,
    shopify_customer_id: str | None,
    customer_woo_customer_id: str | None,
) -> tuple[str | None, CustomerIdentityMethod]:
    """
    Resolve one order to a stable customer identity.

    Priority:

    1. Original non-zero WooCommerce customer ID
       stored on a WooCommerce-origin order.

    2. WooCommerce ID stored on the attached
       Shopify customer.

    3. Shopify Customer ID.

    4. Unresolved.
    """

    if (
        source_system == "woocommerce"
        and order_woo_customer_id is not None
        and order_woo_customer_id != "0"
    ):
        return (
            f"woo:{order_woo_customer_id}",
            CustomerIdentityMethod.WOO_ORDER,
        )

    if (
        customer_woo_customer_id is not None
        and customer_woo_customer_id != "0"
    ):
        return (
            f"woo:{customer_woo_customer_id}",
            CustomerIdentityMethod.WOO_CUSTOMER,
        )

    if shopify_customer_id is not None:
        return (
            f"shopify:{shopify_customer_id}",
            CustomerIdentityMethod.SHOPIFY_CUSTOMER,
        )

    return (
        None,
        CustomerIdentityMethod.UNRESOLVED,
    )


def classify_customer_order(
    *,
    identity_key: str | None,
    seen_identities: set[str],
) -> OrderCustomerClassification:
    """
    Classify one already-qualified order.

    Orders must be processed in chronological order.
    """

    if identity_key is None:
        return OrderCustomerClassification.UNRESOLVED

    if identity_key in seen_identities:
        return OrderCustomerClassification.RETURNING

    seen_identities.add(identity_key)

    return OrderCustomerClassification.NEW