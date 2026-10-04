# Public source-rights review boundary

Status: implemented as a blocked tracking and retrieval-planning contract on
October 4, 2026. It records no permission conclusion and performs no retrieval.

## Purpose

`atlas.source_rights` binds one review entry to every document in the dated
public source-candidate catalog. Version 1 accepts only the explicit
`not_started` state for the `internal_research` use case. Terms URI, terms
evidence digest, review time and validity period must all remain absent.

This narrow first version prevents a public URL, an issuer label or the absence
of a paywall from being interpreted as permission. A later reviewed-evidence
schema is required before Atlas can represent verified or prohibited rights.

## Retrieval plan

The manifest records a conservative future intake envelope:

- at most 5 MiB per source;
- HTML, PDF or JSON only;
- no redirects;
- no source-byte retention; and
- network fetching disabled.

These are planning constraints, not a working downloader. The public summary
omits source and terms URIs, evidence hashes, metrics and recommendations. It
returns blocked until actual terms evidence is reviewed under a future schema.

## Verification

Tests require the review universe and order to equal the source catalog, reject
future/backdated assessments and unsupported use cases, reject unknown fields,
and prevent any rights-state promotion or retrieval-policy relaxation. The CLI
returns a distinct blocked exit code without exposing source or evidence fields.
