# Research extraction-quality contract

`atlas.extraction_quality` records how a metric payload was obtained from exact
source bytes and prevents an extraction from being treated as ready unless its
source, metric, payload, timing and review state agree.

## Evidence

Each immutable record carries a stable extraction, document and metric ID; the
exact source and payload SHA-256 values; the extraction method and version;
extraction time; and a controlled review state. Supported methods are:

- `deterministic_parser`: may use `not_required` when the versioned parser and
  exact contract are the evidence being evaluated.
- `manual_entry`: requires a verified review evidence hash before release.
- `llm_assisted`: requires a verified review evidence hash before release.

`unverified` and `rejected` states never release a metric. A rejected review
retains a review-evidence digest so the decision is auditable without embedding
review notes or source content in the record.

## Release checks

The decision binds the extraction to the same document ID and exact source hash
as `ResearchSourceRecord`, and to the same metric ID and canonical payload hash
as `MetricPayload`. Extraction cannot predate retrieval or occur in the future.
Any failed check returns controlled blocked codes and no extraction ID.

This contract establishes internal traceability, not semantic correctness. A
deterministic parser can consistently extract the wrong field, and a review hash
does not prove reviewer competence or source truth. Provider-specific fixtures,
independent sampling, period/unit reconciliation and error-rate measurement are
still required before a real extractor is accepted.
