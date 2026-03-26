# Garment Production

Garment Production is a Frappe app for textile and garment manufacturing operations. It provides a practical operating model for:

- Raw fabric intake and roll-wise tracking
- Procurement flow with `Purchase Order`, `Purchase Receipt`, and `Purchase Invoice`
- Dyeing batch conversion and wastage capture
- Cutting plans with size-wise output
- Stitching execution and contractor job work
- Quality inspection and rejection control
- Dispatch readiness and customer dispatch
- Sales and cash flow with `Sales Order`, `Sales Invoice`, and `Payment Entry`

## Core DocTypes

- `Garment Style`: style master with customer, item, and consumption defaults
- `Raw Fabric Receipt`: supplier receipt with roll-level details
- `Dyeing Batch`: raw-to-dyed conversion with wastage
- `Cutting Plan`: size-wise cutting output
- `Stitching Job Card`: stitching progress, alter quantity, and rejection
- `Quality Inspection`: passed, rework, and rejected quantities
- `Production Dispatch`: customer dispatch and invoice linkage
- `Contractor Job Work`: outsourced process issue/receipt and payable amount
- `Wastage Entry`: recoverable and non-recoverable waste log

## Standard Charts

- `Raw Fabric Receipt Trend`
- `Stitching Output Trend`
- `QC Passed Quantity`
- `Dispatch Quantity`
- `Job Work Value Trend`
- `Sales Invoice Value Trend`
- `Wastage by Stage`

## Workspace And Alerts

- `Garment Production` workspace with KPI cards, charts, ERP transaction links, and grouped workflow areas
- Sidebar grouped into `Setup`, `Procurement`, `Production`, `Sales & Cash`, and `Control`
- `Production Control Tower` page for raw-fabric-to-cash visibility
- Standard notifications for:
  - contractor job work due reminder
  - QC-ready stitching lots
  - dispatch-ready quality lots
- Daily scheduler summary for system managers covering overdue job work, pending QC, and dispatch-ready lots

## Suggested Flow

1. Create setup masters such as `Garment Style`, `Item`, `Supplier`, `Customer`, `Warehouse`, and UOMs.
2. Raise `Purchase Order` for raw fabric and accessories, then receive them through `Purchase Receipt` and vendor billing through `Purchase Invoice`.
3. Record the inward fabric lot in `Raw Fabric Receipt` for production-side roll tracking.
4. Send material into `Dyeing Batch` or issue it outside through `Contractor Job Work`, depending on whether the process is internal or outsourced.
5. Create `Cutting Plan` from the dyed/processed material and maintain size-wise cut output.
6. Track sewing progress through `Stitching Job Card`, with contractor billing continuing through `Purchase Invoice` where applicable.
7. Approve finished/semi-finished output in `Quality Inspection`, and log scrap/recoverable loss in `Wastage Entry`.
8. Dispatch approved garments with `Production Dispatch`.
9. Complete the sales-to-cash cycle with `Sales Order`, `Sales Invoice`, and `Payment Entry`.

## Notes

- The app is designed as a production-control layer and intentionally keeps accounting integration light.
- Quantity validations enforce that output plus wastage does not exceed input at each stage.
- Contractor billing is estimated from received quantity and rate in `Contractor Job Work`.
- Draft `Purchase Invoice` can be created directly from submitted `Contractor Job Work`.
- Draft `Sales Invoice` can be created directly from submitted `Production Dispatch`.
- Core stages now expose status fields such as cutting, stitching, QC, dispatch, and job-work progress.

## Demo Seed

Use the demo file and seed function to insert 10 end-to-end sample orders with linked procurement, production, sales, and cash-flow records:

```bash
bench --site test execute "garment_production.demo_seed.seed_demo_data"
```
