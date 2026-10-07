# Sample flow (what you type in Studio)

1. Deploy `PolicyChangeDetector` (no constructor arguments).
2. `register_policy`  ->  policy_id: `github-terms`   url: `https://docs.github.com/en/site-policy/github-terms/github-terms-of-service`
3. `check_policy`     ->  policy_id: `github-terms`    (first run = baseline snapshot)
4. Wait, then call `check_policy` again later. If the page changed, you get a record like `sample_record.json`.
5. `get_latest` / `get_record` / `has_material_change_since` read the results.
