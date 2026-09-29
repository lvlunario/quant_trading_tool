# Permitted research-source intake contract

`atlas.source_intake` is the bounded boundary between already-retrieved source
bytes and Atlas's immutable research-source metadata. It does not perform a
network request, follow a URL, parse a metric, persist a document or authenticate
a publisher.

## Admission sequence

1. Require an immutable intake request and exact `bytes` input.
2. Reject empty content and content over 5 MiB.
3. Check the latest data-rights evidence for the exact provider, dataset,
   intended use and intake time. No source record is created unless permission
   is explicit and current.
4. Require strict UTF-8 without NUL for text/JSON/CSV inputs and a PDF header for
   declared PDFs. These are structural sanity checks, not malware scanning or
   authenticity evidence.
5. Validate stable IDs, HTTPS URI and publication/availability/retrieval order.
6. Hash the exact bytes with SHA-256 and return a `ResearchSourceRecord` plus
   byte count. The result retains no source content.

Controlled blocked codes distinguish empty/oversized content, missing or
non-permitted rights, encoding/signature failures and invalid metadata. Invalid
calling types raise `invalid_source_intake_request`.

## Limits

The adapter accepts caller-supplied bytes only. It does not prove that the URI
served those bytes, that the publisher is genuine, that the document is safe or
accurate, or that extracted facts are correct. It has no immutable object store,
duplicate-document ledger, provider-specific downloader, robots/rate-limit
policy, antivirus/sandbox, HTML sanitization or extraction pipeline. Those are
separate controls before live-source ingestion or customer use.
