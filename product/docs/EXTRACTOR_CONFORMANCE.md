# Synthetic extractor conformance contract

`atlas.extractor_conformance` evaluates one fixed invented provider profile
against checked-in positive and negative cases. It answers whether the current
synthetic extractor still behaves exactly as specified; it does not establish
compatibility with a real provider or estimate production accuracy.

## Profile and cases

The versioned manifest binds an opaque profile, provider and dataset ID to one
extractor version and expected metric semantics. Its six required categories
are:

- nominal value extraction;
- explicit missing value;
- unsupported schema version;
- wrong metric identity;
- incompatible unit/currency semantics; and
- wrong reporting-period semantics.

Every case has a stable ID, controlled category, invented source object and
expected accepted/blocked state. The report returns classifications and codes
only; it excludes the source object, formula and reporting dates.

## Sampling policy

The current development policy requires at least six cases, all six categories,
zero false accepts, zero false rejects and zero other expectation mismatches.
Any limit or coverage failure blocks the report. Altering expected values is
therefore visible rather than silently redefining success.

Run the fixed demonstration from `product/`:

```bash
python -m atlas --extractor-conformance-demo
```

## Qualification boundary

Six designed synthetic cases are contract tests, not a statistical sample of
real filings or datasets. Before accepting any real provider extractor, Atlas
still needs authorized representative documents, a privately stored labeled
test set, independent review, provider-format/version coverage, field-level
error measurement, and explicit unit/period reconciliation. Production
acceptance thresholds must be set from that evidence and must not be inferred
from the all-pass synthetic result.
