# Point-in-time observation provenance

Requirements R06 and R15; [tracking issue #4](https://github.com/lvlunario/quant_trading_tool/issues/4). This contract prevents later revisions from silently entering earlier research decisions. It contains synthetic metadata only and does not provide market or fundamental data.

## Record

Each `ObservationRecord` binds one revision of one metric series to:

- stable observation, series and instrument IDs;
- provider, dataset and metric IDs;
- revision number and the period/value `as_of` date;
- `available_at`, when the evidence first became usable, and `observed_at`, when Atlas acquired it;
- HTTPS source URI, exact-source SHA-256 and normalized-payload SHA-256; and
- a versioned transform identifier such as `atlas.fundamentals@1.0.0`.

`available_at` cannot follow `observed_at`, acquisition cannot be future-dated, and revisions in a series must preserve one instrument/provider/dataset/metric/as-of identity. Observation IDs are unique across the evaluated record set and revision numbers are unique within a series. A later revision cannot claim an earlier availability time than its predecessor.

The hashes are integrity/linkage identifiers, not anonymization or proof that the source is accurate. Actual values and licensed source content remain outside this public repository.

## Historical selection

`select_point_in_time(records, series_id, decision_at)` chooses the highest revision whose `available_at` is no later than the decision time. A series unknown to the dataset and a known series not yet available return different missing states. A decision time later than the current evaluation time is invalid.

Example: an original quarterly filing available August 1 and an amendment available September 10 produce different selections for September 1 and September 12. The amendment is never allowed to leak into the September 1 record merely because Atlas downloaded both in September.

Availability is distinct from acquisition. A historically available filing may be loaded by Atlas later and can still support a historical dataset if its availability evidence is reliable. Every revision retains its own source and payload hashes; history is appended, not overwritten.

## Required downstream gates

Selection alone is not research readiness. Before use, the pipeline must also confirm:

1. the `instrument_id` is effective in the security master for the relevant date;
2. current data-rights evidence explicitly permits the intended use;
3. metric units, currency, null policy and transformation are registered; and
4. freshness, reconciliation and quality rules appropriate to the metric pass.

Still pending: the combined readiness gate, persistent private evidence storage, provider adapters, sourced records, corporate actions, macro vintages, transformation registry and experiment/result registry.
