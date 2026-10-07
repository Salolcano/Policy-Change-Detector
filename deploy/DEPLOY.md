# Deploying on Studio Next (no coding needed)

Network: Studio Next
RPC: https://studio-next.genlayer.com/api
Chain ID: 61997
Explorer: https://explorer-studio-dev.genlayer.com/

1. Open GenLayer Studio and connect to Studio Next.
2. Create a new contract file and paste the full text of `contracts/policy_change_detector.py`.
   The first two lines (`# v0.3.0` and the `Depends` line) must stay at the very top.
3. Click Deploy. The constructor has no arguments.
4. Copy the deployed contract address (also visible in the explorer).
5. Try `register_policy` then `check_policy` as shown in `examples/sample_flow.md`.
6. Studio Next charges fees: attach the fee estimate Studio proposes to each write.
