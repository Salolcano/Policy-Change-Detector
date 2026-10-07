# State design

| Field | Type | Meaning |
|---|---|---|
| policies | TreeMap[str, str] | policy_id -> https URL |
| digests | TreeMap[str, str] | policy_id -> compact digest of latest accepted version (the "before" for the next check) |
| counts | TreeMap[str, u256] | policy_id -> number of accepted checks |
| records | TreeMap[str, str] | "policy_id:index" -> JSON record (append-only history) |

Storage is read before the non-deterministic block and written only after consensus is reached.
Records are append-only, so history can never be rewritten.
