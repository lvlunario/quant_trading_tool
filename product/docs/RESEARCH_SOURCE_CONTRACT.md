# Research source-document contract

Status: implemented with synthetic tests on September 28, 2026. This contract
checks internal consistency; it does not authenticate a publisher, prove a
source is accurate, grant data rights or populate a research dataset.

## Purpose

`atlas.source_evidence.ResearchSourceRecord` describes exact bytes retrieved
for one instrument-level research source. It records stable instrument,
provider and dataset IDs; a controlled source kind and content type;
publication, availability and retrieval times; an HTTPS URI; and the exact
SHA-256 digest.

`assess_source_binding` fails closed unless that record agrees with the selected
`ObservationRecord` on instrument, provider, dataset, URI, digest and
availability time. Retrieval must not be in the future or occur after the
observation claims it was observed.

`assess_sourced_metric_input` composes this check with the existing
point-in-time, identity, data-rights, payload-hash and numeric-value gates. A
failed check returns no metric payload.

## Current boundary

- Supported source kinds: issuer filing/release, regulator filing, exchange
  notice and licensed dataset.
- Supported content types: JSON, PDF, CSV and HTML.
- The contract is instrument-level. Macro releases use the separate
  [`MAC_...` vintage contract](MACRO_VINTAGES.md) and are not forced into a fake
  security identity.
- Source classification is asserted metadata, not proof that a domain or
  publisher is genuine. Adapter allowlists, transport capture, immutable
  storage, signature/authority checks and manual source review remain planned.
- Data-rights permission remains a separate gate. A byte-perfect source can
  still be prohibited for the requested use.

## Public candidate catalog

`atlas.source_catalog` adds a narrower, pre-intake boundary for the dated M2
research queue. The checked-in October 3 catalog links the resolved NVDA, MU
and AVGO instrument IDs to official issuer-release HTTPS addresses and their
publication dates. It accepts only the exact three-name universe, the registry's
observation cutoff and an allowlisted issuer domain for each candidate.

A catalog entry is an address to investigate, not a `ResearchSourceRecord`.
The loader therefore requires `rights_state=not_evaluated` and
`extraction_state=not_attempted`; it stores no retrieved bytes or digest and
cannot carry a metric value. Its public summary always reports the metric as
unavailable and blocks progression pending rights and extraction review.

The October 4 [source-rights review boundary](SOURCE_RIGHTS_REVIEW.md) adds an
exact document-level queue and conservative retrieval envelope. It records only
that review has not started and network retrieval remains disabled; it does not
promote any candidate into permitted evidence.

## Verification

Tests cover exact successful binding; instrument/provider/dataset drift;
URI/hash drift; availability/retrieval ordering; future retrieval; invalid
identifiers/types/times; and preservation of prior metric-gate failures. The
candidate-catalog tests separately cover exact universe/order, stable-identity
matching, domain restrictions, cutoff consistency and rejection of prematurely
promoted rights, extraction or metric fields.
