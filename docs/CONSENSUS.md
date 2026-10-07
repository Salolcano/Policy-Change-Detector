# How consensus is used

The page fetch and the model analysis are non-deterministic, so `check_policy` uses a custom
leader/validator pair (`gl.vm.run_nondet_unsafe`), not strict equality.

Leader: fetches the page, hashes the normalized text, asks the model to compare it with the stored
digest, and returns severity, topics, reason and a new digest. Category is derived from severity in code,
so the model cannot return an inconsistent label.

Validators re-fetch and re-analyse independently, then accept only if ALL hold:
1. same category
2. severity differs by at most 1
3. changed topics overlap (Jaccard) >= 50%, using a fixed topic vocabulary so models can agree

The free-text `reason` and `digest` are NOT compared (they will never match word for word); they are bounded
in length and stored from the leader's accepted result. The first check on a policy is a baseline:
validators only need to agree it is a baseline.

Known limits: severity near a band edge (3/4 or 7/8) can cause a disagreement and a retry; pages that
need login or heavy JavaScript may not render.
