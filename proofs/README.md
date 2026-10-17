# StudioNet proofs

Three independent election instances deployed on gasless **StudioNet, chain 61999**. [Successful CLI proof workflow](https://github.com/ehsanisildur-ux/quota-cascade/actions/runs/39040150971) · [45-test CI](https://github.com/ehsanisildur-ux/quota-cascade/actions/runs/39040630587) · [Fresh RPC/source/state verification](verification.json).

All **20** counted receipts are FINALIZED / MAJORITY_AGREE with a strict validator majority. Sixteen executed successfully; four correctly rejected prohibited calls and preserved state. A finalized ERROR is counted only as a rejection proof, never as a successful deployment or ballot. No counted receipt contains a dissenting vote. Eighteen have 3 agree / 0 disagree / 2 idle; the surplus deployment and duplicate-ballot rejection have 5 / 0 / 0. Idle votes are not represented as agreement.

## Contracts and consequential scenarios

| Scenario | StudioNet contract | Deployment | Final count |
|---|---|---|---|
| Fractional surplus | `0xD6C5bB56eb2a8feb414EC8c2f8458514eB707526` | [Deploy](https://explorer-studio.genlayer.com/tx/0x08ff82d429d2b806ffa2ad945c30b31fedda1a0e3506e4deb5b41ec2ee187715) | [Amber + birch](https://explorer-studio.genlayer.com/tx/0x06ee9c4f89a946b47bddb8f6c991a5902821b9610157f09c5bcd3547ca9e2a45) |
| Elimination and corrected preferences | `0xaD73DD1D4203f490EBA5f2a80d392a92Efa9358f` | [Deploy](https://explorer-studio.genlayer.com/tx/0xb047e15c84ad8be63816a3cf5e495918bde7460836ac5d7a12c8a6edf18be4f2) | [Birch](https://explorer-studio.genlayer.com/tx/0x0760615b70778d5576772c8659342aceab3b0f6f7648e2fbc714bc393c86b26a) |
| Unresolved tie and voter abstention | `0xD05480abD6c65E4e27C28452a1E4220bC8E9f18c` | [Deploy](https://explorer-studio.genlayer.com/tx/0x9462e1831f392b80ca23c9db32b234f23c706050df034976c037a7961ddd3306) | [Birch](https://explorer-studio.genlayer.com/tx/0x5b6509e0d2e59be7135efbc26e8b1a42445f127a74a3f63d679b60d2f949db24) |

**Surplus:** weights 6/1/2, two seats, quota 4. Amber's six units transfer at an exact factor of 1/3, leaving four retained and moving two units to birch. Tallies become birch 3 / cedar 2; cedar's elimination transfers two more to birch. The final retained total is nine. [Complete source-bound ballots and count trace](surplus-final-state.json).

**Elimination:** weights 4/3/2, one seat, quota 5. The second voter withdraws an old amber-first draft; the third quotes a colleague before declaring their own cedar-first choice. Consensus records the voters' final personal choices. Cedar's elimination transfers two units to birch, which reaches five and wins; four units remain continuing. [Complete state](elimination-final-state.json).

**Review:** the six-unit voter leaves amber/birch tied, so consensus records REVIEW. Finalization correctly rejects until that same wallet abstains. The original unresolved statement remains in state. A separate explicit reject-all ballot has an empty RANKED order. Only the one-unit birch-first ballot participates; quota is one and birch wins. [Complete state](review-final-state.json).

The three voter wallets are distinct and every signature is checked against the expected roster. A fourth, non-admitted wallet finalizes all three elections. All four are controlled by the test runner; this demonstrates contract authorization rather than independent real-world voters. GenLayer validators supply the independent source interpretation. Ballot documents are synthetic and public.

## Full transaction ledger

Each label links to its explorer transaction. Full raw receipts use the corresponding `<label>-receipt.json` filename. State-changing proofs additionally retain before/after snapshots; rejected-call proofs preserve decoded error messages.

| Label | Execution | Agree/disagree/idle |
|---|---|---|
| [surplus-deployment](https://explorer-studio.genlayer.com/tx/0x08ff82d429d2b806ffa2ad945c30b31fedda1a0e3506e4deb5b41ec2ee187715) | SUCCESS | 5/0/0 |
| [unauthorized](https://explorer-studio.genlayer.com/tx/0x4659765a56c4c9741b249c7bd5ab85b90f4ea1bf1b455256fadb1c75190f0ce9) | ERROR, voter not admitted | 3/0/2 |
| [bad-hash](https://explorer-studio.genlayer.com/tx/0x3b7a3f91fb9923d33cc4d5a9d19105146b7cf21eb9bad7ed06630a3a38a9a5c0) | ERROR, commitment mismatch | 3/0/2 |
| [surplus-cast-0](https://explorer-studio.genlayer.com/tx/0x8e3a6cf83b7bc8f84c1476f07f8bd6cb7d4329fa2ba9b6b9345f47d4925378e8) | SUCCESS | 3/0/2 |
| [surplus-cast-1](https://explorer-studio.genlayer.com/tx/0x50ee7f00ca7ea064d58caaeae0c34ea347a6d6cbbc4446c2b2eec8ed56e93540) | SUCCESS | 3/0/2 |
| [surplus-cast-2](https://explorer-studio.genlayer.com/tx/0x402739f2069e91e728124f6cddd8d05d3820dfc22ef5837e40784e5eb2150f81) | SUCCESS | 3/0/2 |
| [duplicate](https://explorer-studio.genlayer.com/tx/0x9ba08eefb5cc69cee909d8bce1bc9c5a970a4c65be2b4bf56e51374af5f3c9dd) | ERROR, ballot already submitted | 5/0/0 |
| [surplus-finalize](https://explorer-studio.genlayer.com/tx/0x06ee9c4f89a946b47bddb8f6c991a5902821b9610157f09c5bcd3547ca9e2a45) | SUCCESS | 3/0/2 |
| [elimination-deployment](https://explorer-studio.genlayer.com/tx/0xb047e15c84ad8be63816a3cf5e495918bde7460836ac5d7a12c8a6edf18be4f2) | SUCCESS | 3/0/2 |
| [elimination-cast-0](https://explorer-studio.genlayer.com/tx/0xe085d0e8fa32aae2e9ff7e31649dcea7516f21d2ccc33ebe2fb47baf6ae87dcb) | SUCCESS | 3/0/2 |
| [elimination-cast-1](https://explorer-studio.genlayer.com/tx/0x5d4e3ea20b8802acc7b34cbc46fb9c3ceee7631f8d2577b0b66c975a409203ab) | SUCCESS | 3/0/2 |
| [elimination-cast-2](https://explorer-studio.genlayer.com/tx/0x6f62d41af56af410a09194ee7d9c9aa61a6ea957b5310d48dc3c7af2cc22d93e) | SUCCESS | 3/0/2 |
| [elimination-finalize](https://explorer-studio.genlayer.com/tx/0x0760615b70778d5576772c8659342aceab3b0f6f7648e2fbc714bc393c86b26a) | SUCCESS | 3/0/2 |
| [review-deployment](https://explorer-studio.genlayer.com/tx/0x9462e1831f392b80ca23c9db32b234f23c706050df034976c037a7961ddd3306) | SUCCESS | 3/0/2 |
| [review-cast-0](https://explorer-studio.genlayer.com/tx/0x8b6b541b79385dc56edfd1d0eb05d2b27bfd67dda2663dea2e859e41fabe9c36) | SUCCESS | 3/0/2 |
| [review-cast-1](https://explorer-studio.genlayer.com/tx/0x9eb5210b64fb824ff476f7d78d16eb51259285168ff99a83ec54db066f35fc68) | SUCCESS | 3/0/2 |
| [review-cast-2](https://explorer-studio.genlayer.com/tx/0xdf8a106264071acd7b70dc804be829f11ec663019d3868b2069eff8b5255d789) | SUCCESS | 3/0/2 |
| [review-blocked](https://explorer-studio.genlayer.com/tx/0x98b2dd80bea2c81d6fa1ac5419c3850b1665c4eb7dc8d693ebb0abd642b68c5c) | ERROR, every voter must rank or abstain | 3/0/2 |
| [review-abstain](https://explorer-studio.genlayer.com/tx/0x1b1842ad4d81280b1581a2d390cd1e294d7217a446ed74c0dc32b07d931b0233) | SUCCESS | 3/0/2 |
| [review-finalize](https://explorer-studio.genlayer.com/tx/0x5b6509e0d2e59be7135efbc26e8b1a42445f127a74a3f63d679b60d2f949db24) | SUCCESS | 3/0/2 |

## Source and verification binding

Deployed source revision: `4db35a22dbc68aa31b7cbff44212b6ebb7e8c2ef`.

Exact source SHA-256: `b5260c35d4d1dac51a5288b879e7eaf0c7e212cde644a4148329df72d1105907`.

Commit-pinned ballot revision: `b371d68e6d047f4a6ffef92c391ad7c6427a3a7f`. [Deployment manifests](deployments.json) retain each URL, SHA-256, full statement and actual voter roster.

`verify-proofs.cjs` independently re-fetches all twenty receipts, verifies strict majorities, execution outcomes, sender/destination binding and saved votes, compares all three deployed source files byte-for-byte, and re-reads final states. `check-state.py` reconstructs every round using a separate Fraction parcel ledger without importing the contract. Offline verification checks saved artifacts without replacing fresh verification metadata.

The live workflow passed 37 direct tests at its source revision. The later test-only revision adds eight roster rejection cases: current local tests and public CI pass **45**. Both reports are retained as `cloud-direct-tests.xml` and `local-direct-tests.xml`. Contract code is unchanged between these revisions.

[Earlier rejected constructor receipt](rejected-constructor-39039492892/README.md) is preserved separately and excluded from all successful deployment claims and the twenty-receipt proof set.
