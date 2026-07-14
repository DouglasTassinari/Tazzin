# Synthetic data generation

`scripts/generate_synthetic_data.py` builds a coherent, multi-year
dataset for a fictional company. "Coherent" specifically means: most
tables are not populated independently with random values — they are
**derived from upstream activity**, so the dashboards tell one consistent
story instead of showing disconnected random numbers.

## Generation order (dependency order)

1. **Reference data**: Locations (8: plants/warehouses/offices) →
   Departments (10) → Employees (260) → Warehouses (5) → Products (130) →
   Production lines (12) → Customers (240) → Suppliers (95) → Roles (5) →
   Users (70, linked to a random subset of employees).
2. **Primary activity**: Sales orders (~2,200, 1–5 line items each) →
   Purchase orders (~950, 1–6 line items each) → Production work orders
   (~1,700, with start/stop events).
3. **Derived activity**:
   - **Stock movements** — one OUTBOUND movement per sales order line, one
     INBOUND movement per purchase order line, plus ~1,200 standalone
     adjustment/transfer movements for texture.
   - **Finance ledger** — Invoices generated from a sample of
     shipped/invoiced sales orders (receivable) and received purchase
     orders (payable); paid invoices get a matching pair of Transactions
     (cash + revenue/COGS side); a monthly payroll Transaction is posted
     for every month in the dataset, sized to the active headcount's
     total base salary.
4. **Supporting activity**: Time-off requests (650, scoped to each
   employee's actual tenure) → Projects (42, with 6–18 tasks and 2–5
   milestones each) → Maintenance assets/requests/logs (210 assets, ~850
   requests) → Quality inspections/nonconformances/metrics (~2,400
   inspections, with nonconformances only raised for non-passing
   inspections) → Audit log entries (350).

## Approximate row counts (seed 42)

| Table | Rows |
|---|---|
| sales_orders / sales_order_items | 2,200 / 6,600 |
| purchasing_orders / purchasing_order_items | 950 / 3,300 |
| production_work_orders / production_events | 1,700 / 3,100 |
| inventory_stock_movements | 10,700 |
| finance_invoices / finance_transactions | 1,900 / 3,700 |
| people_employees / people_timeoff_requests | 260 / 650 |
| projects / projects_tasks / projects_milestones | 42 / 520 / 130 |
| maintenance_assets / requests / logs | 210 / 850 / 1,350 |
| quality_inspections / nonconformances / metrics | 2,400 / ~410 / 690 |
| machining_appointments (machines / operators) | 4,500 (12 / 14) |
| machining_scrap_records / scrap_parts | 380 / 50 |
| machining_time_adjustments | 220 |
| **Total across 38 tables** | **~46,000** |

## Realism choices worth knowing about

- **Quality results are derived from a beta distribution** skewed toward
  low defect rates (`random.betavariate(0.5, 45)`), so ~83% of
  inspections PASS, ~16% go to REWORK, under 1% FAIL — tuned to look like
  a functioning quality process rather than a coin flip.
- **Invoice status** depends on how long ago the due date was: invoices
  due more than 45 days before "today" are mostly PAID; recent ones are
  a mix of OPEN/OVERDUE — so the Finance dashboard shows a believable
  aging pattern instead of random statuses.
- **Employment status** is 90% ACTIVE / 5% ON_LEAVE / 5% TERMINATED.
- The dataset window is **2023-01-01 to the current date**, so every run
  produces a dataset that ends "today" without manual date updates.

## Re-running with a different seed

```bash
python scripts/generate_synthetic_data.py --reset --seed 7
```

Same code path, different `random`/`Faker` seed — useful for confirming
the dashboards hold up against more than one dataset shape.
