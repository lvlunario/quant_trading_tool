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

## Reviewed-evidence schema

`atlas.rights_evidence` provides that separate schema without changing the
blocked queue. Each immutable record binds an opaque review ID and reviewer
reference to the exact document/symbol/use case, terms URI and SHA-256 evidence,
terms observation time, review time, validity deadline, conclusion and permitted
actions. Conclusions are `permitted`, `prohibited` or `needs_counsel`.

For internal research, an explicitly permitted decision must include both
`retrieve_once` and `extract_internal`. Optional private retention or excerpt
citation is recorded separately. Customer display and redistribution require
different future use-case reviews; they cannot enter this schema as actions.

The manual checklist is exact and ordered:

1. identify the source owner;
2. capture the terms version;
3. evaluate the intended use;
4. evaluate automated access;
5. evaluate retention;
6. evaluate display;
7. evaluate redistribution; and
8. set an expiry or re-review date.

Missing, conflicting, expired, prohibited, counsel-required or incomplete-action
evidence blocks. Public summaries omit terms URIs, evidence hashes, review IDs
and reviewer references. A passing rights decision still reports technical
retrieval disabled and release authorization false.

## Blank review worksheet

`python -m atlas --rights-review-worksheet-demo` binds every current source
candidate to one blank review task. The template includes the public document
and source address, the exact reviewed-evidence field names, allowed conclusions
and actions, and all eight checklist steps marked `pending`. It carries no
terms address, hash, reviewer reference, conclusion or permitted-action value.

Completed worksheets and captured terms evidence must be stored only in the
approved private boundary outside this repository. Generating the worksheet is
work preparation, not a completed review, legal advice, permission, retrieval
enablement or release authorization.

The Research workbench projects only aggregate readiness from this template:
eight reviews pending, zero of 64 per-source checklist steps complete, private
evidence storage required, retrieval disabled and release unauthorized. It does
not expose source addresses, document/review identifiers or evidence fields.

## Technical source-capture authorization

`python -m atlas --source-capture-authorization-demo` combines the rights
decision with a separate exact-document technical approval. Both must be
current before capture can be authorized. Approvals permit only one bounded
capture, at most 5 MiB, using HTML/PDF/JSON without redirects or byte retention.
The checked-in evidence and approval sets authorize zero captures. The receipt
contains no approval ID, document ID, source/terms address, evidence hash or
reviewer reference and never authorizes release.

The Research workbench renders only candidate, rights-ready and authorized
counts plus source-byte absence and release false. It does not display approval
or document identifiers, source/terms addresses, hashes or reviewer references.

## Public M2 gate trace

`python -m atlas --m2-acceptance-trace` composes the exact checked-in identity,
source, rights and capture decisions into ordered aggregate counts. Extraction
and metric release remain zero because no authorized source bytes or verified
metric evidence are accepted by this trace version. This is engineering
readiness evidence, not a completed rights review, milestone acceptance or
release authorization.

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

Queue tests require the review universe and order to equal the source catalog, reject
future/backdated assessments and unsupported use cases, reject unknown fields,
and prevent any rights-state promotion or retrieval-policy relaxation. The CLI
returns a distinct blocked exit code without exposing source or evidence fields.
Reviewed-evidence tests cover the complete checklist, timing, exact identities,
unique review IDs, action scope, latest-review selection, same-time conflicts,
expiry and redacted reporting. The public evidence register remains empty.
