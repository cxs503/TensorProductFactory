# Production-order execution

The first order-level runner is a deterministic, one-tick orchestrator. It is
intentionally not a daemon or distributed scheduler.

## Persistence

- `SQLiteProductionStore` stores immutable ProductSpec versions and
  ProductionOrders. Each order references an exact product/version pair.
- `SQLiteWorkOrderStore` stores the task DAG, mission links, output refs, and
  optimistic revisions.
- Both adapters are file-backed, single-node MVP stores. They are not a shared
  multi-worker database.

## One execution tick

`advance_production_order` performs these steps:

1. Load the ProductionOrder and its exact ProductSpec version.
2. Load and validate the WorkOrder DAG; reject cross-order tasks, missing
   dependencies, duplicate IDs, or cycles.
3. Poll linked Platform missions and persist changed task snapshots.
4. Treat Platform `succeeded` / `awaiting_acceptance` as WorkOrder
   `SUBMITTED`, never as product acceptance.
5. Dispatch READY tasks only when every dependency is independently
   `ACCEPTED`. Stable WorkOrder IDs remain the Platform `task_key`.
6. Move the ProductionOrder to `PRODUCING`, `QA`, or `FAILED` based on
   persisted task outcomes. Reaching `QA` does not release the product.

The caller may invoke one tick from a scheduler, CLI, or service loop. Repeated
ticks are safe for already-linked missions and only dispatch newly eligible
READY tasks. Network and compare-and-swap failures are surfaced to the caller;
a retry reconciles through the stable task key.

## Deliberate boundaries

- Product-level QA, manifest creation, and release remain separate gates.
- The runner does not create WorkOrders from a ProductSpec automatically.
- It does not start a background process, claim live Agent execution, or
  synthesize output assets.
- TensorData registration, packaging/delivery, payments, and sales metrics
  are not implemented by this slice.
