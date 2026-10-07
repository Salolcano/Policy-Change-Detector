"""Pure-logic tests. Run with:  python -m pytest tests/test_equivalence.py
They load the helper block straight out of the contract file, so no genlayer install is needed."""
import pathlib

SRC = (pathlib.Path(__file__).parent.parent / "contracts" / "policy_change_detector.py").read_text()
BLOCK = SRC.split("# --- pure helpers begin")[1].split("# --- pure helpers end ---")[0]
BLOCK = BLOCK.split("\n", 1)[1]  # drop the rest of the marker line
NS = {}
exec("import json, hashlib, re\n" + BLOCK, NS)

parse_analysis = NS["parse_analysis"]
results_equivalent = NS["results_equivalent"]
category_from_severity = NS["category_from_severity"]
text_hash = NS["text_hash"]


def mk(sev, topics):
    return {"severity": sev, "category": category_from_severity(sev), "changed_topics": sorted(topics)}


def test_category_bands():
    assert [category_from_severity(s) for s in (0, 1, 3, 4, 7, 8, 10)] == [
        "none", "minor", "minor", "material", "material", "breaking", "breaking"]


def test_hash_ignores_whitespace_and_case():
    assert text_hash("Hello   World\n") == text_hash("hello world")


def test_parse_clamps_and_filters_topics():
    raw = '```json\n{"severity": 99, "changed_topics": ["ARBITRATION", "bogus", "arbitration"], "reason": "x", "digest": "d"}\n```'
    out = parse_analysis(raw)
    assert out["severity"] == 10 and out["category"] == "breaking"
    assert out["changed_topics"] == ["arbitration"]


def test_parse_rejects_garbage():
    try:
        parse_analysis("no json here")
        assert False
    except ValueError:
        pass


def test_equivalent_within_tolerance():
    assert results_equivalent(mk(5, ["fees_billing", "retention"]), mk(6, ["fees_billing", "retention"]), False)


def test_rejects_category_mismatch():
    assert not results_equivalent(mk(3, ["other"]), mk(4, ["other"]), False)  # minor vs material


def test_rejects_severity_gap():
    assert not results_equivalent(mk(5, ["other"]), mk(7, ["other"]), False)


def test_rejects_low_topic_overlap():
    assert not results_equivalent(mk(5, ["fees_billing"]), mk(5, ["arbitration"]), False)


def test_baseline_only_needs_baseline_on_both_sides():
    a = {"category": "baseline", "severity": 0, "changed_topics": []}
    assert results_equivalent(a, dict(a), True)
    assert not results_equivalent(a, mk(5, []), True)
