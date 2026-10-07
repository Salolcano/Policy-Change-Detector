"""Integration tests against GenLayer Studio / localnet.
Setup:  pip install genlayer-test   then   gltest tests/integration
(API names follow the genlayer-test package; adjust if your installed version differs.)"""
from gltest import get_contract_factory
from gltest.assertions import tx_execution_succeeded

URL = "https://example.com/terms"


def deploy():
    return get_contract_factory("PolicyChangeDetector").deploy(args=[])


def test_register_and_read():
    c = deploy()
    tx = c.register_policy(args=["acme-tos", URL]).transact()
    assert tx_execution_succeeded(tx)
    assert c.get_policy(args=["acme-tos"]).call() == URL
    assert c.list_policies().call() == ["acme-tos"]
    assert c.get_check_count(args=["acme-tos"]).call() == 0


def test_duplicate_id_is_rejected():
    c = deploy()
    c.register_policy(args=["a", URL]).transact()
    tx = c.register_policy(args=["a", URL]).transact()
    assert not tx_execution_succeeded(tx)


def test_non_https_is_rejected():
    c = deploy()
    tx = c.register_policy(args=["a", "http://example.com"]).transact()
    assert not tx_execution_succeeded(tx)


def test_first_check_is_baseline():
    c = deploy()
    c.register_policy(args=["a", URL]).transact()
    tx = c.check_policy(args=["a"]).transact()
    assert tx_execution_succeeded(tx)
    assert c.get_check_count(args=["a"]).call() == 1
    assert '"category": "baseline"' in c.get_latest(args=["a"]).call()
