# Modules

Each module follows the same five-file pattern described in
[`ARCHITECTURE.md`](ARCHITECTURE.md). This is a functional reference —
what each module tracks and the KPIs its page shows.

| Module | Entities | Page KPIs |
|---|---|---|
| **Sales** | Customer, SalesOrder, SalesOrderItem | Net revenue in period, active customers, revenue by month, top 10 customers |
| **Production** | ProductionLine, WorkOrder, ProductionEvent | Work orders in period, average yield %, total scrap, yield by line, scrap by month |
| **Inventory** | Warehouse, Product, StockMovement | Active SKUs, low-stock product count, total on-hand units, top 15 products by on-hand |
| **Purchasing** | Supplier, PurchaseOrder, PurchaseOrderItem | Total spend, active suppliers, average rating, spend by month, top 10 suppliers |
| **Finance** | Account, Invoice, Transaction | Outstanding receivables/payables, net cashflow, cashflow by month |
| **People** | Department, Employee, TimeOffRequest | Active headcount, pending time-off requests, approved days, headcount by department |
| **Projects** | Project, Task, Milestone | Active projects, average completion rate, upcoming milestones, completion rate by project |
| **Maintenance** | Asset, MaintenanceRequest, MaintenanceLog | Open requests, total cost in period, critical assets, cost by month, open requests by priority |
| **Quality** | Inspection, NonConformance, QualityMetric | Average defect rate, open nonconformances, pass rate, defect rate by month, open NC by severity |
| **Administration** | Role, User, AuditLog | Active users, system health status, uptime, per-operation call/latency/error metrics, recent audit events |
| **Analytics** (Dashboard) | *(no tables — composes the services above)* | Revenue, spend, net cashflow, active projects, avg production yield, avg defect rate, open maintenance requests, active headcount, outstanding receivables/payables |

## Status-transition rules

Several modules model a lifecycle as an explicit state machine in their
`domain/*_rules.py`, guarded by `can_transition()` / `assert_transition()`:

- **Sales** `OrderStatus`: DRAFT → CONFIRMED → SHIPPED → INVOICED (or CANCELLED from DRAFT/CONFIRMED)
- **Production** `WorkOrderStatus`: PLANNED → IN_PROGRESS → COMPLETED (or CANCELLED)
- **Purchasing** `PurchaseOrderStatus`: DRAFT → SENT → CONFIRMED → RECEIVED (or CANCELLED)
- **Finance** `InvoiceStatus`: OPEN → PAID / OVERDUE → PAID (or CANCELLED)
- **Projects** `ProjectStatus`: PLANNING → ACTIVE → ON_HOLD/COMPLETED (or CANCELLED)
- **Maintenance** `MaintenanceStatus`: OPEN → SCHEDULED → IN_PROGRESS → COMPLETED (or CANCELLED)
- **Quality** `NonConformanceStatus`: OPEN → UNDER_REVIEW → RESOLVED → CLOSED

Attempting a disallowed transition raises `ValidationError` — this is
covered directly in each module's `tests/test_domain/test_<module>_rules.py`.

## Cross-module id references (no ORM relationships)

| Referencing module | Column | Points at |
|---|---|---|
| Sales | `SalesOrderItem.product_id` | Inventory `products` |
| Production | `WorkOrder.product_id` | Inventory `products` |
| Purchasing | `PurchaseOrderItem.product_id` | Inventory `products` |
| Quality | `Inspection.product_id` | Inventory `products` |
| Quality | `Inspection.work_order_id` | Production `work_orders` |
| Finance | `Invoice.source_sales_order_id` / `source_purchase_order_id` | Sales / Purchasing orders |
| People | `Employee.location_id` | core `Location` |
| Projects | `Task.assignee_employee_id`, `Project.sponsor_department_id` | People `employees` / `departments` |
| Maintenance | `MaintenanceRequest.requested_by_employee_id` | People `employees` |
| Administration | `User.employee_id` | People `employees` |

See [`ARCHITECTURE.md § Module boundaries`](ARCHITECTURE.md#module-boundaries)
for why these are plain FK columns rather than `relationship()` objects.
