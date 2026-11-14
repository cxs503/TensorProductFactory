# TensorProductFactory

TensorProductFactory is the product-production layer for discovering, specifying, producing, independently validating, releasing, and learning from sellable digital products.

It orchestrates existing Tensor infrastructure rather than reimplementing agent execution, data storage, knowledge governance, or benchmarking.

## Responsibilities

- Define market opportunities and versioned product specifications.
- Create production orders and dependency-aware work orders.
- Aggregate versioned assets into a product manifest with source, checksum, and rights state.
- Require independent, evidence-backed QA and cleared rights for required assets before release.
- Track immutable release package references and real commercial outcomes.

## System boundaries

- **TensorPlatform** executes agent missions and manages runtime orchestration.
- **TensorData** stores and versions governed assets.
- **TensorKnowledge** records claims, evidence, and provenance.
- **TensorBench** provides reproducible benchmark execution and evaluation evidence.
- **TensorProductFactory** owns product lifecycle, product-level acceptance, and release decisions.

A completed Platform mission, registered Data asset, reviewed Knowledge evidence, or passing Bench run is not by itself approval to sell a product.

## Current implementation

- Typed product, production-order, work-order, QA, asset-manifest, and release records.
- Explicit work-order transition guard and dependency DAG validation/topological scheduling.
- Product release-candidate checks for QA verdict, version consistency, and required asset rights.
- Manifest assembly from submitted task outputs, requiring explicit hashes, provenance, and rights metadata.
- Rule-profile-driven independent QA with explicit missing-evidence findings, plus a product acceptance gate that only accepts submitted work after a passing QA report.
- TensorPlatform MissionCreate payload mapping plus an authenticated HTTP client, stable-task-key retry behavior, mission polling, and execution-state synchronization.
- Dependency-gated dispatch orchestration joining the WorkOrder store, idempotent Platform client, and mission-state synchronization.
- File-backed SQLite WorkOrder persistence with optimistic concurrency control. Deployment credentials and Factory Profile project registration remain operator-supplied.
- JSON Schema contracts, pytest tests for domain rules and Platform adapter/client behavior, and a GitHub Actions CI workflow.

See [TensorPlatform integration](docs/platform-integration.md) for API configuration and dispatch/polling semantics.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Status

Early implementation. Tests are authored but must be executed in CI or a development environment before merge. No claim of production readiness, live integration, or commercial validation is made.
