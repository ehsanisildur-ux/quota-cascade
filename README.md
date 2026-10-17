# QuotaCascade

Source-grounded ranked ballots become an exact, auditable multi-seat election.

QuotaCascade is a standalone GenLayer voting primitive. A deployment freezes 3–5 candidate IDs, 1–8 voter wallets with fixed weights, 1–3 seats, an election ID and a publisher repository. Each admitted wallet submits one commit-pinned prose ballot. The contract downloads full bytes, verifies SHA-256 and binds the statement to that wallet's immutable voter ID and election. A publisher cannot cast a ballot on a voter's behalf.

The leader extracts the voter's final strict ranking. Validators independently fetch the full statement, derive their own ranking and require exact status/order agreement. They also audit every omission and source anchor. Quoted opinions, withdrawn drafts, ties and missing comparisons receive explicit treatment. REVIEW cannot participate in counting: the voter must explicitly abstain, preserving the original statement and decision. Valid submitted rankings are immutable.

Once every voter ranks or abstains, anyone finalizes. The contract uses a fixed Droop quota, inclusive Gregory fractional surplus transfers, full-value elimination transfers and reduced integer fractions. Each round records tallies, transfer factor, locked weight, exhausted weight and continuing weight. Their sum must equal the original participating weight. This is an actual stateful election with wallet admission and final seat assignment, rather than a renamed comparison tournament or graph-edit workflow.

- [Pinned contract](contracts/quota_cascade.py)
- [Consensus and counting specification](docs/architecture.md)
- [Direct tests and independent Fraction oracle](tests/direct/test_cascade.py)
- [Synthetic ballot statements](ballots)
- [Live proof status](proofs/README.md)
- [Submission draft](docs/submission.md)

## Verification

```sh
pip install -r requirements-dev.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/quota_cascade.py --json
python -m pytest -q
```

The manual GitHub proof workflow creates encrypted disposable CLI accounts, deploys on gasless StudioNet (chain 61999), and uploads sanitized receipts. It verifies execution success, finalized strict-majority agreement, exact source bytes and independent state/count results. A successful CLI banner alone is insufficient.

## Scope

Ballots and voter wallets are public. The constructor decides eligibility, weights, candidate IDs and tie priority; validators do not establish whether that electorate is legitimate. A voter authorizes a specific published revision by sending its commitment, not by proving who wrote the prose. There is no external election certification, secret voting, coercion resistance, token custody or execution of winners' real-world powers. Synthetic statements demonstrate semantics. No claim of universal architectural originality or review acceptance is made.
