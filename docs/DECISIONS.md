## Historical Commerce Provenance

### Decision

Historical order provenance is determined per order, not by a fixed Shopify migration date.

WooCommerce-origin orders imported through Matrixify are identified using both:

* Shopify `sourceName = "Matrixify App"`; and
* the presence of the WooCommerce order ID metafield `woo.id_`.

Source-system mapping:

* Matrixify + WooCommerce order ID -> `woocommerce`
* Matrixify without WooCommerce order ID -> `matrixify_unknown`
* other Shopify order sources -> `shopify`

### Historical Order Date

`processedAt` is used as `reporting_order_at`.

Historical audits across 2021 through September 2024 showed that Matrixify `createdAt` values represent migration/import timing while `processedAt` preserves the historical WooCommerce purchase timestamp.

Raw Shopify timestamps are retained separately.

### Customer Identity

Order-level WooCommerce customer ID and customer-level WooCommerce ID are retained independently.

They must not currently be assumed to be interchangeable because migration audits found mismatches and guest-order edge cases.

Cross-platform customer identity will be resolved only after the complete historical dataset is loaded and audited.

### Payment Status

The existing successful-payment rule remains:

A successful Shopify `SALE` or `CAPTURE` transaction establishes successful payment.

Audited Matrixify WooCommerce orders from 2021 through September 2024 preserved successful `SALE` transactions for paid orders. Cancelled/unpaid examples did not.

### Rationale

The migration contained overlapping Matrixify and native Shopify activity, so a date-based migration boundary would misclassify orders. Preserving explicit source metadata and unresolved cases provides a more reliable foundation for historical reporting and customer acquisition analysis.
