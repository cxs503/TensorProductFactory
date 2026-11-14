# TensorProductFactory

TensorProductFactory is the product-production layer for discovering, specifying, producing, independently validating, releasing, and learning from sellable digital products.

It orchestrates existing Tensor infrastructure rather than reimplementing agent execution, data storage, knowledge governance, or benchmarking.

## Responsibilities

- Define market opportunities and versioned product specifications.
- Create production orders and dependency-aware work orders.
- Aggregate versioned assets into a product manifest.
- Require independent, evidence-backed QA before release.
- Track release packages and real commercial outcomes.

## System boundaries

- **TensorPlatform** executes agent missions and manages runtime orchestration.
- **TensorData** stores and versions governed assets.
- **TensorKnowledge** records claims, evidence, and provenance.
- **TensorBench** provides reproducible benchmark execution and evaluation evidence.
- **TensorProductFactory** owns product lifecycle, product-level acceptance, and release decisions.

A completed Platform mission, registered Data asset, reviewed Knowledge evidence, or passing Bench run is not by itself approval to sell a product.

## Initial implementation

The first milestone defines typed domain objects, lifecycle transition rules, JSON Schemas, and tests. Platform/Data/Knowledge/Bench integrations will be adapters with explicit contracts; unavailable remote APIs will not be assumed.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```

## Status

Early implementation. No claim of production readiness or commercial validation is made.