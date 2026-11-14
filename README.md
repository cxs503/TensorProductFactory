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
- Explicit work-order transition guard.
- Product release-candidate checks for QA verdict, version consistency, and required asset rights.
- Pure TensorPlatform MissionCreate payload mapping; this is not a live API client and does not bypass Platform repository allowlisting.
- JSON Schema contracts and pytest tests.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Status

Early implementation. Tests are authored but must be executed in CI or a development environment before merge. No claim of production readiness, live integration, or commercial validation is made.
