# Architecture and integration boundaries

## Product lifecycle ownership

TensorProductFactory owns product-level state and the decision to release a product. External systems provide execution, assets, knowledge evidence, and benchmark evidence; none of those systems can independently authorize a release.

## Core mappings

| Factory object | External system | Mapping |
|---|---|---|
| WorkOrder | TensorPlatform Mission | WorkOrder ID becomes idempotency key task_key; objective becomes goal; acceptance criteria are passed as criteria statements. |
| Platform project | TensorPlatform Mission | Mission repo is a project key configured in FACTORY_PROFILE.projects, not a GitHub owner/repository slug. The key must be allowlisted and resolve to a local Git checkout on the worker. |
| Worker role | TensorPlatform Mission | Product roles and Platform worker roles are separate vocabularies. The adapter requires an explicit supported Platform role; it never guesses a role mapping. |
| Budget | TensorPlatform Mission | Factory budget units are not silently converted to Platform's structured budget object. The caller must provide a separately approved Platform budget policy. |
| Execution reference | TensorPlatform Mission | Persist returned mission_id and observed execution status. The current adapter only builds a request payload; it does not make a network call. |
| Product asset reference | TensorData | Persist immutable asset identifier, version, checksum, rights state, and source. |
| Evidence reference | TensorKnowledge | Link evidence/provenance records; evidence registration is not product approval. |
| Benchmark evidence | TensorBench | Link reproducible run/result artifact; passing a benchmark is not whole-product approval. |

## Acceptance invariants

1. The producer cannot be the sole reviewer approving their own work.
2. Every passing QA rule must link to evidence.
3. Platform mission completion means execution ended, not that the product passed QA.
4. A product release must pin an immutable product version and its asset manifest.
5. Missing rights, unresolved critical defects, or missing required evidence block release.
6. Commercial metrics must originate from real order/payment/refund records; estimates must be labelled as estimates.
7. WorkOrder dependencies are a ProductFactory DAG. TensorPlatform's parent_mission_id is a single-parent execution relation and must not be assumed to encode an arbitrary multi-parent dependency graph.

## Initial scope

This MVP implements typed core records, release-candidate checks, explicit work-order state transitions, JSON Schema contracts, and a pure Platform MissionCreate payload mapper. It does not yet implement persistence, live API calls, dispatch retries, webhook/polling synchronization, Data/Knowledge/Bench adapters, release signing, or payment integration.
