# Daily Commercial Report V1

## Purpose

Provide a trusted daily view of Super Speciosa commercial performance using reconciled source data.

The first version combines:

* Shopify sales
* customer acquisition
* Meta advertising spend
* manual marketing spend

Subscription, Everflow, and GA4 reporting are excluded from V1.

## Reporting Period

Default reporting period:

* yesterday
* compared with the previous day
* compared with the same weekday one week earlier

Additional supported periods should later include:

* last 7 days
* previous 7 days
* month to date
* previous month-to-date equivalent

Business timezone: TBD before final reporting implementation.

Currency: USD.

Incomplete current-day data should not be included in standard daily reporting.

## Sales Metrics

### Qualifying Orders

A qualifying order:

* has a successful payment;
* is not a test order;
* is not cancelled; and
* has product revenue greater than $0.

### Product Revenue

Product revenue is:

* after discounts;
* excluding shipping;
* excluding tax; and
* excluding fees.

Refunds do not rewrite original order revenue.

### Order Count

Number of qualifying orders.

### Average Order Value

Product revenue divided by qualifying orders.

### Refunds

Reported separately from original sales.

Include:

* number of refund events;
* total cash refunded;
* product refund amount where attributable;
* shipping refund amount where attributable;
* tax refund amount where attributable.

Refund reporting uses the refund date.

## Customer Metrics

### New Customer Orders

The customer's first-ever qualifying order across the complete WooCommerce and Shopify history.

### Returning Customer Orders

Every qualifying order after the customer's first qualifying order.

### New Customers

Unique customers placing their first qualifying order during the reporting period.

### Returning Customers

Unique customers placing one or more returning qualifying orders during the reporting period.

New-versus-returning reporting must not be released until historical customer identity resolution has been validated.

## Marketing Spend

### Meta Spend

Actual advertising spend reported by Meta for the reporting period.

### Manual Spend

Delivered / recognized marketing costs from the controlled manual spend ledger.

Examples:

* sponsorships
* creators
* newsletter placements
* podcast placements
* agency costs
* offline marketing

### Total Marketing Spend

Meta spend plus recognized manual marketing spend included under the agreed reporting definition.

Costs already represented in Meta must not be counted again through invoices or manual records.

## Efficiency Metrics

### Blended Marketing Efficiency

Product revenue / total marketing spend

This is a blended business metric and must not be described as platform-attributed ROAS.

### Blended New-Customer Acquisition Cost

Agreed acquisition spend / new customers

This is a blended acquisition metric and does not imply that every new customer was caused by paid advertising.

### Meta Platform ROAS

Meta-attributed revenue / Meta spend

This must remain separate from Shopify-observed revenue and blended business efficiency.

## Data Freshness

Every report should state freshness for:

* Shopify
* Meta
* manual spend

Example:

> Shopify complete through yesterday. Meta spend complete through yesterday. Manual spend last updated September 24.

## Data Quality

The report should warn when:

* a source import has failed;
* a source is stale;
* manual spend is incomplete;
* customer classification is unresolved;
* historical coverage is incomplete;
* a material reconciliation check has failed.

A missing source must never silently appear as zero.

## Initial Daily Output

The first daily report should show:

### Sales

* product revenue
* qualifying orders
* average order value
* refunds

### Customer Acquisition

* new customers
* new customer orders
* returning customers
* returning customer orders

### Marketing

* Meta spend
* manual spend
* total marketing spend

### Efficiency

* blended marketing efficiency
* blended new-customer acquisition cost
* Meta platform ROAS

### Comparisons

For each key metric:

* reporting-period value
* comparison-period value
* absolute change
* percentage change where meaningful

## V1 Acceptance Criteria

The report is ready for use when:

1. Shopify figures reconcile to source data.
2. Complete historical customer order history has been loaded.
3. Customer identity rules have been validated.
4. New-versus-returning classification has been manually checked against real customer histories.
5. Meta spend reconciles to Meta for selected test periods.
6. Manual spend records can be imported without duplicates.
7. Marketing spend cannot be dou
