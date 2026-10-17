# Consensus boundary and election rules

## Public workflow

`QuotaCascade(publisher, election, candidates_json, voters_json, seats)` fixes the rules. Voter rows are `{id,address,weight}` with unique IDs and nonzero unique addresses. Weights are integers 1–20. No administrator or mutable roster exists.

`cast(url,sha256)` is admitted-wallet-only, once per voter. The URL must name `ballots/*.json` at a full 40-character Git commit inside the frozen repository. Complete UTF-8 bytes (at most 8000) must match SHA-256. JSON rejects duplicate keys and binds election and voter ID. Only prose paragraphs contain preference information; callers never provide machine-readable rankings.

`abstain()` is admitted-wallet-only and permitted only for PENDING or REVIEW. An unresolved ballot remains available in full after abstention. RANKED and ABSTAIN cannot be revised. `finalize()` is permissionless after every voter has RANKED or ABSTAIN status. It writes the result exactly once. There is intentionally no timeout or power to exclude an unresponsive voter: a missing or unresolved vote can block liveness. Deployments must choose a cooperative bounded electorate.

## Consequential nondeterminism

Leader and validators independently download and hash the full source. Each interprets final strict order, explicit exclusions, corrections, quoted speech and unresolved ambiguity. Exact status and ordered-ID agreement is required, without confidence tolerances. A separate validator audit checks the leader's selected paragraph and every omission in the context of the entire source, including negative decisions. Paragraph selection can differ between independent extractions; the leader's anchor must still pass the material audit.

An incomplete or tied preference returns REVIEW with an empty order. Explicit rejection of all candidates returns RANKED with an empty order; it is excluded from participating weight. Missing information never becomes rejection. External deterministic errors require exact agreement; shared transient fetch failures may agree only as failed transactions. LLM/schema errors cannot authorize acceptance. Accepted source and decisions are preserved in onchain state.

## Exact inclusive Gregory count

Initial ballot weight equals its roster weight. ABSTAIN and empty rankings do not contribute to total or quota. Quota is `floor(total/(seats+1))+1` and never changes when votes exhaust. With no participating weight, result is NO_VOTES with no winners.

For each round, every ballot's remaining fractional weight belongs to its first continuing candidate, or to exhaustion if none remains. If the number of continuing candidates is at most the number of vacant seats, elect the earliest continuing candidate and retain its full tally. This standard completion rule can fill a seat with a zero-support candidate; the trace makes this explicit. Otherwise elect the largest tally at or above quota. Retain quota and multiply every ballot assigned to that elected candidate by `(tally-quota)/tally`. If nobody reaches quota, eliminate the lowest tally and transfer its assigned ballots at full remaining weight.

Candidate-order ties favor earlier constructor positions for election and later positions for elimination. These disclosed deterministic choices are not random fairness. Every elected or eliminated candidate leaves the continuing set; at most five rounds run. All arithmetic uses reduced numerator/denominator integer pairs. On each round, retained + exhausted + continuing = initial total is checked exactly. After the final seat, residual continuing weight is retained as trace information rather than transferred unnecessarily. Winner indices map to constructor candidate order.

## Distinct mechanism

QuotaCascade's wallet-specific irrevocable ballots, participant abstention gate, seat quota, parcel-weight decay, exhaustion and final seat assignment differ from strongest-path pairwise choice, stable matching, owner graph transitions and certificates. Semantic consensus controls which preferences can move each voter's weight. Deterministic arithmetic alone cannot supply those rankings.

## Tests and public proof limits

Direct tests invoke actual GenVM methods and explicitly replay validator callbacks; ordinary direct execution alone runs only the leader. A separate Python Fraction parcel ledger checks 2000 combinations of full and truncated rankings against the contract's rational engine, including exact actions and transfer factors. Live workflows use three distinct disposable wallets. They are controlled by one test runner and do not demonstrate organizational voter independence. Network validators supply the independent GenLayer assessment.

Bounds make exhaustive trace auditing feasible; this is not a claim of suitability for a large public election. This count is the disclosed inclusive Gregory variant, not every jurisdiction's STV rules. Publisher integrity, voter legitimacy, coercion and actual external seat powers remain consumer responsibilities.
