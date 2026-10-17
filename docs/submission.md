Category: Builder → Intelligent Contracts

Title: QuotaCascade: Consensus ranked ballots with exact surplus transfers

QuotaCascade turns prose ballots into a bounded GenLayer multi-seat election. Fixed voter wallets authorize commit-pinned statements. Leader and validators independently fetch full texts, check SHA-256, interpret final strict rankings and audit every omission and source anchor. Exact status/order agreement controls transferable vote weight. Unresolved ties block counting until that voter abstains. A fixed Droop quota, exact inclusive Gregory surplus fractions and elimination transfers assign seats; each round conserves retained, continuing and exhausted weight. Three StudioNet elections prove fractional surplus, corrected/quoted preferences and review-to-abstention. All 20 receipts finalized MAJORITY_AGREE, including four unchanged-state rejections. The repo includes 45 direct tests, validator replay and 2000 complete traces checked by an independent Fraction oracle. Synthetic public ballots test the mechanism; roster legitimacy and external seat powers remain outside it.

Repository: https://github.com/ehsanisildur-ux/quota-cascade

Contract: https://github.com/ehsanisildur-ux/quota-cascade/blob/main/contracts/quota_cascade.py

Proofs: https://github.com/ehsanisildur-ux/quota-cascade/blob/main/proofs/README.md

StudioNet contract: `0xD6C5bB56eb2a8feb414EC8c2f8458514eB707526`

Deployment: https://explorer-studio.genlayer.com/tx/0x08ff82d429d2b806ffa2ad945c30b31fedda1a0e3506e4deb5b41ec2ee187715
