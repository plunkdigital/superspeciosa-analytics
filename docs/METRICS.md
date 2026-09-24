# Super Speciosa Reporting Metrics

## 1. Qualifying Order

A **qualifying order** is a Shopify order that:

* has been successfully paid;
* is not a test order;
* has not been cancelled; and
* has an order value greater than $0, excluding shipping, tax, and fees.

Orders with $0 product/order value do not count as qualifying orders, even if shipping, tax, or other fees were charged.

A later refund does not cause an otherwise qualifying order to stop being a qualifying order.

---

## 2. Revenue

**Revenue** is the value of the qualifying order after discounts, excluding:

* shipping;
* tax; and
* fees.

Refunds do not retrospectively remove an order from revenue/order reporting.

Revenue is recorded against the original order.

Example:

* Products after discounts: $100
* Tax: $7
* Shipping: $5
* Total charged: $112
* Super Speciosa revenue: **$100**

---

## 3. Refunds

Refunds are reported separately from orders and revenue.

An order remains present in order reporting after a refund.

The order reporting table should show:

* whether the order has been refunded;
* whether the refund is partial or full;
* total amount refunded; and
* remaining revenue after refunds.

Partial refunds are supported.

Reporting convention:

* order reporting uses the original order date;
* refund reporting uses the date the refund was processed;
* refunds do not rewrite historical order counts.

This allows an order and its subsequent refund to remain independently visible.

---

## 4. New Customer

A customer is a **new customer** when they place their first qualifying order with an order value greater than $0.

That order is classified as a:

**New Customer Order**

Orders that are:

* $0 orders;
* test orders; or
* cancelled orders

do not establish a customer's first qualifying purchase.

---

## 5. Returning Customer

After a customer has placed their first qualifying order, every subsequent qualifying order is classified as a:

**Returning Customer Order**

At the time of those subsequent orders, the customer is classified as a:

**Returning Customer**

The classification is based on the customer's qualifying order history, not merely the date range being reported.

For example, if a customer's first qualifying order occurred in January and they place another order in September, the September order is a returning customer order even if a report only covers September.

---

## 6. Refunds and Customer Classification

Refunds do not rewrite customer acquisition history.

If a customer's first qualifying order is subsequently partially or fully refunded, it remains their first qualifying order.

A later qualifying purchase is still classified as a returning customer order.

---

## 7. Customer Identity

Customer classification requires orders belonging to the same person to be linked consistently.

Initial identity rule:

1. Use Shopify Customer ID where available.
2. If Shopify Customer ID is unavailable, use a controlled fallback identity method.

The fallback method will be defined after inspecting the Shopify source data.

---

## 8. Core Order Reporting Fields

The initial order reporting dataset should make the following available:

* Shopify order ID
* Shopify order number
* order timestamp
* customer identifier
* new / returning classification
* qualifying order status
* order revenue
* shipping amount
* tax amount
* fees, where applicable
* refunded amount
* refund status
* remaining revenue after refunds
* payment status
* cancellation status
* test order status
* Shopify last-updated timestamp
* data ingestion timestamp
