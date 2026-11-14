# TensorPlatform integration

## API configuration

Construct `TensorPlatformClient` with:

- `api_base_url`: the deployment's API root ending in `/api/v1` (for example, `https://host.example/api/v1`). Do not include `/tensor/missions`.
- `token`: a short-lived bearer token for a TensorPlatform account authorized to create missions (ADMIN, MANAGER, or ENGINEER). Do not commit tokens or place them in ProductSpec/WorkOrder metadata.
- `timeout_seconds`: request timeout; default 20 seconds.
- `retries`: transient failure retries; default 2.

## Dispatch protocol

1. ProductFactory first verifies that every dependency is independently accepted.
2. Use `dispatch_work_order` to enforce READY state and independently accepted dependencies before any network call.
3. The helper builds the MissionCreate body and calls `TensorPlatformClient.create_mission`. The WorkOrder ID is sent as `task_key`; Platform enforces idempotency for the same authenticated organization and rejects reuse with a different task definition (409).
4. Persist the returned mission ID by applying `attach_mission` and saving the updated WorkOrder. `SQLiteWorkOrderStore` provides a file-backed MVP store with optimistic revision checks; it is a single-node adapter, not a shared production database.
5. Agent completion must put stable asset references in the Platform completion `summary.output_refs` list (the Platform API persists that summary as mission `result`). Poll `get_mission` to refresh the execution snapshot. `sync_work_order` maps Platform states to ProductFactory execution states and strictly validates/collects `result.output_refs`; malformed references fail closed.
6. Run ProductFactory's own evidence-backed QA. Platform `awaiting_acceptance` / `completed` is only a submitted execution result, never ProductFactory `ACCEPTED`.

## Important constraints

- The API user must have permission to create missions. A normal agent account may not be authorized.
- The project ID must exist in the running Platform Factory Profile and resolve to a local Git checkout on the worker host. This is a deployment configuration step, not something this client can create remotely.
- Platform's mission API accepts structured budget limits. Domain integer budgets are not automatically converted; pass a Platform budget policy explicitly.
- The current Platform API accepts acceptance criteria as strings or objects and freezes their canonical form. Keep criteria immutable after dispatch.
- ProductFactory supports multi-parent DAGs. Platform's `parent_mission_id` is a single-parent field; do not use it as a replacement for ProductFactory dependency enforcement.
- Mission creation retries reuse the same `task_key`; do not change the task definition while retrying an uncertain request.
- This client does not claim that a mission has been claimed, executed, accepted, or delivered. Only subsequent API reads can establish those facts.


## Durable work-order state

`SQLiteWorkOrderStore` persists work orders between dispatch and polling. The intended sequence is: create the work order in the store; create the Platform mission; attach the returned mission ID; update the stored row using its current revision; later reload the row, poll `get_mission`, call `sync_work_order`, and update again using the newly read revision.

A revision mismatch raises `ConcurrentWorkOrderUpdate`; callers must reload and reconcile rather than overwrite newer state. Store the database on persistent storage and back it up. SQLite is intended for a single-node MVP; multi-worker deployments need a shared transactional database adapter.
