# Project State

## Current Status

The Shopify commercial-data foundation is working against the live Super Speciosa store.

### Verified

* Supabase Postgres connection is working.
* Alembic migrations are working.
* Shopify Dev Dashboard app is installed and authenticated.
* Required Shopify read scopes are available.
* Shopify orders can be queried through the Admin GraphQL API.
* Order mapping is covered by automated tests.
* Recent Shopify orders successfully map into the normalized database schema.
* Imports are idempotent.
* Database records reconcile exactly against Shopify for:

  * order count;
  * product revenue;
  * shipping; and
  * tax.
* A closed 6-day period reconciled successfully.
* August 2026 reconciled successfully:

  * 11,155 orders
  * $1,135,511.73 product revenue
  * $109,762.62 shipping
  * $51,900.24 tax
* Historical range imports use pagination and batched database writes.
* Large-order pagination guards are in place.
* Refund structures have been inspected against real Shopify data.
* Full and partial refunds are stored separately from original order revenue.

## Historical Data Findings

The store migrated from WooCommerce to Shopify during 2024 using Matrixify.

Historical inspection established:

* WooCommerce-origin orders are present in Shopify as Matrixify imports.
* Matrixify orders can overlap in date with native Shopify orders, so there is no reliable date-only migration boundary.
* Legacy provenance must be determined per order.
* Matrixify-imported WooCommerce orders generally contain:

  * `sourceName = "Matrixify App"`
  * WooCommerce order ID in the `woo.id_` metafield
  * WooCommerce customer ID in the `woo.customer_id` metafield where available
* Native Shopify-era orders generally use other source values such as `web`, subscription, draft-order, or app-specific sources.
* Shopify `createdAt` is not the historical purchase date for Matrixify imports.
* Shopify `processedAt` consistently reflects the original historical WooCommerce purchase date in audited samples from 2021 through September 2024.
* `processedAt` is therefore the current reporting-order timestamp for both legacy and native orders.
* Imported paid WooCommerce orders contain successful Shopify `SALE` transactions in audited samples.
* The existing successful-payment rule can therefore remain unchanged.

## Customer Identity Findings

Historical customer linkage is not perfectly clean.

The September 2024 audit found:

* 3,183 registered Matrixify orders where the order WooCommerce customer ID matched the attached Shopify customer's WooCommerce ID.
* 68 registered orders with mismatched or missing WooCommerce customer linkage.
* 541 WooCommerce guest orders attached to Shopify customers that have WooCommerce IDs.
* 934 guest orders without a WooCommerce customer link.

Therefore:

* Shopify Customer ID alone must not yet be treated as the final cross-platform customer identity.
* Order-level WooCo

## Historical Shopify Backfill

Complete through August 2026.

Coverage begins in July 2016.

The historical dataset includes:

- WooCommerce-origin orders imported through Matrixify
- native Shopify orders
- draft-order sources
- subscription-order sources
- other Shopify-era application sources

Each closed monthly range was imported idempotently and reconciled against Shopify for:

- order count
- product revenue
- shipping
- tax

Historical edge cases handled during backfill:

- exact month-end timestamp boundaries
- WooCommerce IDs imported with `.0` suffixes
- orders with more than 50 line items
- overlapping WooCommerce/Shopify migration activity
- Matrixify orders without identifiable WooCommerce order IDs
- legacy pending orders without payment evidence

The next major task is customer identity resolution and first-ever qualifying-order classification.