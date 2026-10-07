# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

import json
import hashlib
import re

import genlayer as gl
from genlayer.types import *


# --- pure helpers begin (no genlayer imports below this line until "pure helpers end") ---

CATEGORIES = ["none", "minor", "material", "breaking"]

TOPIC_VOCAB = [
    "data_collection",
    "data_sharing",
    "retention",
    "arbitration",
    "liability",
    "fees_billing",
    "termination",
    "ai_training",
    "user_content_rights",
    "age_restrictions",
    "cookies_tracking",
    "governing_law",
    "other",
]

MAX_PAGE_CHARS = 12000
MIN_TOPIC_OVERLAP = 0.5
MAX_SEVERITY_GAP = 1


def normalize_text(raw: str) -> str:
    """Collapse whitespace so cosmetic page differences do not change the hash."""
    return re.sub(r"\s+", " ", raw).strip().lower()


def text_hash(raw: str) -> str:
    return hashlib.sha256(normalize_text(raw).encode("utf-8")).hexdigest()


def category_from_severity(severity: int) -> str:
    if severity <= 0:
        return "none"
    if severity <= 3:
        return "minor"
    if severity <= 7:
        return "material"
    return "breaking"


def parse_analysis(raw: str) -> dict:
    """Turn the model output into a clean, bounded dict. Raises ValueError if unusable."""
    cleaned = raw.replace("```json", "").replace("```", "")
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object in model output")
    data = json.loads(cleaned[start : end + 1])

    severity = int(data.get("severity", 0))
    severity = max(0, min(10, severity))

    topics = []
    for t in data.get("changed_topics", []):
        t = str(t).strip().lower()
        if t in TOPIC_VOCAB and t not in topics:
            topics.append(t)
    topics.sort()

    digest = str(data.get("digest", "")).strip()[:1500]

    return {
        "severity": severity,
        "category": category_from_severity(severity),
        "changed_topics": topics,
        "reason": str(data.get("reason", "")).strip()[:400],
        "digest": digest,
    }


def topic_overlap(a: list, b: list) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def results_equivalent(leader: dict, mine: dict, baseline: bool) -> bool:
    """Validator rule: same category, severity within +-1, topics overlap >= 50%."""
    if baseline:
        # first snapshot: only require that both sides agree it is a baseline
        return leader["category"] == "baseline" and mine["category"] == "baseline"
    if leader["category"] != mine["category"]:
        return False
    if abs(leader["severity"] - mine["severity"]) > MAX_SEVERITY_GAP:
        return False
    if topic_overlap(leader["changed_topics"], mine["changed_topics"]) < MIN_TOPIC_OVERLAP:
        return False
    return True

# --- pure helpers end ---


class PolicyChangeDetector(gl.contract.Contract):
    # policy_id -> page url
    policies: gl.storage.TreeMap[str, str]
    # policy_id -> short digest of the latest accepted version (used as the "before" next time)
    digests: gl.storage.TreeMap[str, str]
    # policy_id -> number of accepted checks
    counts: gl.storage.TreeMap[str, u256]
    # "policy_id:index" -> JSON record of one accepted check
    records: gl.storage.TreeMap[str, str]

    def __init__(self) -> None:
        pass

    # ---------- writes ----------

    @gl.public.write
    def register_policy(self, policy_id: str, url: str) -> None:
        if len(policy_id) == 0 or len(policy_id) > 64:
            raise gl.vm.UserError("policy_id must be 1-64 characters")
        if not url.startswith("https://"):
            raise gl.vm.UserError("url must start with https://")
        if self.policies.get(policy_id, "") != "":
            raise gl.vm.UserError("policy_id already registered")
        self.policies[policy_id] = url
        self.counts[policy_id] = u256(0)

    @gl.public.write
    def check_policy(self, policy_id: str) -> str:
        url = self.policies.get(policy_id, "")
        if url == "":
            raise gl.vm.UserError("unknown policy_id")

        # read storage BEFORE the non-deterministic block
        previous_digest = self.digests.get(policy_id, "")
        baseline = previous_digest == ""

        def analyse() -> str:
            page = gl.nondet.web.render(url, mode="text")
            body = normalize_text(page)[:MAX_PAGE_CHARS]
            fingerprint = text_hash(page)

            if baseline:
                task = f"""
You summarise legal policy pages. Read the page below and write a compact digest
(max 10 short lines) of the current stance on each of these topics when present:
{", ".join(TOPIC_VOCAB)}.

PAGE:
{body}
END PAGE

Respond ONLY with JSON, no other words or formatting:
{{"severity": 0, "changed_topics": [], "reason": "baseline snapshot", "digest": "<digest text>"}}
"""
            else:
                task = f"""
You compare two versions of a legal policy page.

PREVIOUS DIGEST:
{previous_digest}

CURRENT PAGE:
{body}
END PAGE

Rate how much the CURRENT page changes what a user has agreed to, compared with the digest.
severity is an integer 0-10:
0 = no substantive change (wording, formatting, dates only)
1-3 = minor (clarifications, contact details, small additions)
4-7 = material (new data use, new fees, narrower rights, new obligations)
8-10 = breaking (arbitration/waiver of rights, AI training on user content, major liability shift, termination of core rights)
changed_topics must only use values from: {", ".join(TOPIC_VOCAB)}.
digest is an updated compact digest of the CURRENT page (max 10 short lines).

Respond ONLY with JSON, no other words or formatting:
{{"severity": int, "changed_topics": [str], "reason": str, "digest": str}}
"""
            raw = gl.nondet.exec_prompt(task)
            result = parse_analysis(raw)
            if baseline:
                result["category"] = "baseline"
                result["severity"] = 0
                result["changed_topics"] = []
            result["text_hash"] = fingerprint
            return json.dumps(result, sort_keys=True)

        def validate(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                leader = json.loads(leader_result.calldata)
                mine = json.loads(analyse())
            except Exception:
                return False
            return results_equivalent(leader, mine, baseline)

        final = gl.vm.run_nondet_unsafe(analyse, validate)
        result = json.loads(final)

        index = int(self.counts.get(policy_id, 0))
        record = {
            "index": index,
            "category": result["category"],
            "severity": result["severity"],
            "changed_topics": result["changed_topics"],
            "reason": result["reason"],
            "text_hash": result["text_hash"],
        }
        self.records[f"{policy_id}:{index}"] = json.dumps(record, sort_keys=True)
        self.digests[policy_id] = result["digest"]
        self.counts[policy_id] = u256(index + 1)
        return json.dumps(record, sort_keys=True)

    # ---------- views ----------

    @gl.public.view
    def get_policy(self, policy_id: str) -> str:
        return self.policies.get(policy_id, "")

    @gl.public.view
    def list_policies(self) -> list[str]:
        return [k for k, _ in self.policies.items()]

    @gl.public.view
    def get_check_count(self, policy_id: str) -> int:
        return int(self.counts.get(policy_id, 0))

    @gl.public.view
    def get_record(self, policy_id: str, index: int) -> str:
        return self.records.get(f"{policy_id}:{index}", "")

    @gl.public.view
    def get_latest(self, policy_id: str) -> str:
        n = int(self.counts.get(policy_id, 0))
        if n == 0:
            return ""
        return self.records.get(f"{policy_id}:{n - 1}", "")

    @gl.public.view
    def has_material_change_since(self, policy_id: str, index: int) -> bool:
        """Composable primitive: did any check after `index` rate material or breaking?"""
        n = int(self.counts.get(policy_id, 0))
        for i in range(index + 1, n):
            rec = json.loads(self.records.get(f"{policy_id}:{i}", "{}"))
            if rec.get("category") in ("material", "breaking"):
                return True
        return False
