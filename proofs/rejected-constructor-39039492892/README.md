# Rejected constructor attempt

Workflow: https://github.com/ehsanisildur-ux/quota-cascade/actions/runs/39039492892

Transaction: https://explorer-studio.genlayer.com/tx/0x4426f039f5a752eda59e01942cfb825d76dcec02fdcb136ecd86064df9dafd8e

Source revision: `3305e4dcf499ac4e59b01e7383b1c59d03417e50`.

The receipt finalized MAJORITY_AGREE with execution ERROR: `[EXPECTED] Invalid weighted voter`. Four validators agreed and one was idle. This is **not a deployed working contract** and is excluded from the successful proof set. The CLI recursively converted JSON address strings into native calldata addresses, which that constructor's string-only roster validator rejected. The corrected constructor accepts native typed candidate/ID/address/weight arrays and tests actual SDK Address objects.

An earlier workflow, `39039147631`, failed in account-address discovery before the deployment step. It submitted no deployment transaction. Setup now reads only public address metadata from encrypted CLI keystores.
