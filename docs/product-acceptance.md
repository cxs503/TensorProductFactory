# Product asset and acceptance flow

The product QA boundary is deliberately later than Agent execution:

```text
Platform Mission
  -> WorkOrder SUBMITTED + output_refs
  -> asset ingestion supplies SHA256, source_ref, version, role, rights_status
  -> ProductManifest
  -> versioned QARuleProfile + independent evidence
  -> QAReport
  -> WorkOrder ACCEPTED
  -> Release candidate
```

## 1. Build the manifest before final acceptance

Use `build_product_manifest` with WorkOrders in `SUBMITTED` state. Every output URI must have explicit metadata:

- stable `asset_id` and asset `version`
- semantic `role` (chapter, source, executable, image, audio, etc.)
- SHA-256 digest of the actual bytes
- `source_ref` identifying the originating mission or upstream source
- `rights_status` from the rights review workflow
- optional boolean `required` (defaults to true)

The builder refuses missing metadata, malformed hashes, and tasks that have not submitted. It does not calculate a hash from a URI and does not infer rights from the producer.

## 2. Run a versioned QA profile

A `QARuleProfile` declares the product mode and required rule IDs. Keep profile versions immutable once used for a release decision. Evidence must be keyed by those rule IDs; missing evidence becomes an explicit `needs_rework` finding, and unexpected rule IDs are rejected.

Passing evidence must cite at least one evidence reference. The reviewer must not appear among producer IDs. The resulting `QAReport` records the profile ID and version.

## 3. Product acceptance

`accept_submitted_work_orders` is the only lifecycle helper that moves submitted work orders to `ACCEPTED`. It checks:

- all work orders belong to the same ProductionOrder and are SUBMITTED
- QA report belongs to that ProductionOrder
- QA verdict is PASS and its version matches the manifest
- every submitted output reference appears in the manifest
- every required manifest asset has cleared rights

A Platform mission marked succeeded is not enough. A ProductFactory QA PASS is not enough if the manifest is incomplete or rights are unresolved.

## 4. Current boundary

This is an executable domain/lifecycle layer, not yet an end-to-end TensorData ingestion connector. The caller must obtain real asset bytes, compute SHA-256, register or resolve the asset in TensorData, and provide verified provenance and rights metadata. ProductFactory currently validates those supplied facts; it does not fabricate them or claim a Data registration occurred.
