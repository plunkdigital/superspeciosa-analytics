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

## Legacy WooCommerce Payment Evidence

### Decision

Historical WooCommerce orders imported through Matrixify use the same successful-payment rule as native Shopify orders:

A successful Shopify `SALE` or `CAPTURE` transaction is required for an order to qualify as successfully paid.

Historical audits found that paid and refunded WooCommerce orders were imported with successful Shopify sale transactions.

Some early WooCommerce orders were imported with:

* `displayFinancialStatus = PENDING`;
* no successful Shopify payment transaction;
* no WooCommerce transaction ID; and
* no separate capture evidence.

These orders remain in the historical dataset but do not qualify as sales.

Positive product value alone is not evidence of successful payment.

### Rationale

The reporting definition requires a successfully paid order. Treating historical pending orders as sales without payment evidence would introduce unsupported revenue and customer-acquisition history.

## Large Historical Orders

Orders with unusually high line counts, quantities, or revenue are preserved as normal source records.

They are not automatically classified as wholesale.

A later analysis will identify large-order candidates across the full historical dataset and determine whether a defensible wholesale classification can be established.

## Customer Identity and New vs Returning Classification

### Canonical Identity Resolution

Qualifying orders are resolved to customer identities using the following priority:

1. For WooCommerce-origin orders with a non-zero order-level WooCommerce customer ID:
   - `woo:<order woo customer id>`

2. Otherwise, when the attached Shopify customer has a migrated WooCommerce customer ID:
   - `woo:<customer woo id>`

3. Otherwise, when a Shopify customer exists:
   - `shopify:<shopify customer id>`

4. Otherwise:
   - unresolved

The original WooCommerce customer ID stored on an order takes precedence over the customer attached by Matrixify because historical migration audits found cases where those values disagree.

### New Customer Order

The first qualifying order belonging to a resolved customer identity is classified as a new customer order.

### Returning Customer Order

Every later qualifying order belonging to that identity is classified as a returning customer order.

Classification uses the complete available WooCommerce and Shopify purchase history.

### Unresolved Orders

Qualifying orders without a defensible customer identity remain classified as unresolved.

They:

- remain included in total order and revenue reporting;
- are not counted as new customers;
- are not counted as returning customers; and
- are disclosed separately where customer-mix reporting is presented.

Manual review found that most unresolved Shopify-era orders relate to customers whose accounts were deleted. Historical unresolved WooCommerce records will not be manually reconstructed unless a future business requirement justifies the effort.

### Validation

Cross-platform customer histories were manually spot-checked.

The reviewed histories consistently showed:

- the first qualifying WooCommerce order classified as new;
- later WooCommerce orders classified as returning; and
- later Shopify orders continuing as returning after the migration.

The identity and classification rules are therefore approved for reporting.