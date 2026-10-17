Category: Builder → Intelligent Contracts

Title: QuotaCascade: Consensus ranked ballots with exact surplus transfers

QuotaCascade turns published prose ballots into a bounded onchain multi-seat election. Admitted wallets commit one source revision; leader and validators independently fetch full texts, check SHA-256, interpret final strict rankings and audit omissions and anchors. Exact status/order agreement controls each voter's transferable weight. Ties or incomplete rankings block finalization until the voter explicitly abstains. A fixed Droop quota, exact inclusive Gregory surplus fractions and elimination transfers assign seats with deterministic tie priority. Every round preserves retained, continuing and exhausted vote weight. Tests replay validators and compare 2000 ranking systems against an independent Fraction oracle. Synthetic public ballots demonstrate the mechanism; eligibility and weights are deployment choices, ballots are public, and winners receive no external powers automatically.

Repository: https://github.com/ehsanisildur-ux/quota-cascade

Contract: https://github.com/ehsanisildur-ux/quota-cascade/blob/main/contracts/quota_cascade.py

Proofs: https://github.com/ehsanisildur-ux/quota-cascade/blob/main/proofs/README.md
