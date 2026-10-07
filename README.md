# Policy Change Detector (GenLayer Intelligent Contract)

A standalone contract primitive that watches a policy / Terms of Service page and records
consensus-backed change classifications on-chain.

- Contract: `contracts/policy_change_detector.py`
- Why it exists: `docs/PURPOSE.md`
- How consensus works: `docs/CONSENSUS.md`
- State layout: `docs/STATE_DESIGN.md`
- Deploy on Studio Next: `deploy/DEPLOY.md`
- Example inputs/outputs: `examples/`

## Methods
| Method | Type | What it does |
|---|---|---|
| register_policy(policy_id, url) | write | add a policy to watch (https only, unique id) |
| check_policy(policy_id) | write | fetch, analyse, reach consensus, store a record |
| get_policy / list_policies | view | read registered policies |
| get_check_count / get_record / get_latest | view | read history |
| has_material_change_since(policy_id, index) | view | composable flag for other contracts |

## Tests
- Logic tests (needs only pytest): `python -m pytest tests/test_equivalence.py`
- Integration tests: `pip install genlayer-test` then `gltest tests/integration`

## Deployed
Studio Next address: _fill in after deploy_
