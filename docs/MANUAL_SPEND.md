# Manual Marketing Spend

## Purpose

Capture marketing costs that are not reliably available through an automated advertising platform.

The database will ultimately be the reporting source of truth, but the initial input mechanism will be a controlled CSV or spreadsheet.

## Initial Cost Types

- Sponsorship
- Creator / influencer
- Affiliate
- Agency
- Newsletter placement
- Podcast placement
- Offline advertising
- Other marketing

## Required Fields

Each spend record should contain:

- stable record ID
- vendor
- channel
- campaign / placement
- cost type
- amount
- currency
- service start date
- service end date
- status
- invoice / supporting reference
- notes

## Reporting Rule

Marketing spend is recognized according to the period in which the marketing activity is delivered, not simply when an invoice is paid.

Example:

A $6,000 placement running during September and paid in October contributes $6,000 to September marketing spend.

## Double Counting

A payment or invoice that settles advertising spend already imported from an advertising platform must not be counted as additional marketing spend.

## Initial Status Values

- planned
- approved
- delivered
- cancelled

Only delivered / recognized spend should enter actual performance reporting unless a report explicitly requests committed or planned spend.