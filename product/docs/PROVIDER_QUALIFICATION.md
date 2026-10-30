# Private provider-extractor qualification protocol

`atlas.provider_qualification` defines the evidence required before Atlas can
call a real research-data extractor technically qualified. The protocol can be
reviewed publicly; its documents, labels, reviewer identities and receipts must
remain in an approved private boundary.

## Adopted technical thresholds

- at least 30 representative authorized documents;
- at least 200 independently checked fields;
- at least 99% exact field matches;
- every declared supported format/version tested;
- zero critical false acceptances;
- zero metric-identity, unit, currency or reporting-period mismatches;
- at least two distinct reviewers; and
- current private-boundary and purpose-authorization receipts.

These are conservative minimum engineering gates, not a statistical confidence
claim. A provider-, format- or risk-specific review may require a larger sample
or stricter thresholds. Unsupported formats remain unsupported rather than
being excluded from the denominator.

## Fail-closed decision

Evidence binds the exact provider, dataset and extractor version. Missing,
expired, future-dated, synthetic-only or mismatched evidence returns `blocked`.
The public-safe report contains counts, rates and controlled decision codes; it
excludes document content, digests, receipt IDs and reviewer identifiers.

Run the current no-evidence status from `product/`:

```bash
python -m atlas --provider-qualification-demo
```

The command intentionally exits with blocked status while no authorized private
evidence exists. A technical `qualified_private` result would still set
`release_authorized` to false. Founder acceptance, data rights, legal review,
security readiness and production release remain separate gates.
