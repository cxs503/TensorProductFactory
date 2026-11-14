# Architecture and integration boundaries

## Product lifecycle ownership

TensorProductFactory owns product-level state and the decision to release a product. External systems provide execution, assets, knowledge evidence, and benchmark evidence; none of those systems can independently authorize a release.

## Core mappings

| Factory object | External system | Mapping |
|---|---|---|
| WorkOrder | TensorPlatform Mission | `work_order_id -> task_key`, objective -> goal, worker_role -> worker_role, acceptance criteria -> acceptance_criteria, budget -> budget |
| execution reference | TensorPlatform Mission | Persist returned `mission_id` and observed execution status |
| Product asset reference | TensorData | Persist immutable asset identifier, version, checksum, rights state, and source |
| Evidence reference | TensorKnowledge | Link evidence/provenance records; evidence registration is not product approval |
| Benchmark evidence | TensorBench | Link reproducible run/result artifact; passing a benchmark is not whole-product approval |

## Acceptance invariants

1. The producer cannot be the sole reviewer approving their own work.
2. Every passing QA rule must link to evidence.
3. Platform mission completion means execution ended, not that the product passed QA.
4. A product release must pin an immutable product version and its asset manifest.
5. Missing rights, unresolved critical defects, or missing required evidence block release.
6. Commercial metrics must originate from real order/payment/refund records; estimates must be labelled as estimates.

## Initial scope

This MVP implements typed core records and the work-order state transition guard. Network adapters, persistence, release signing, and payment/order integrations are intentionally not represented as implemented.
