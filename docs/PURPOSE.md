# Purpose

Terms of Service and privacy policies change quietly. Contracts and apps that depend on a policy
(e.g. "the user agreed to X") have no trustworthy way to know when the deal changed.

PolicyChangeDetector is a reusable primitive: it watches a public policy URL and writes an
on-chain, consensus-backed record of each change: category (none / minor / material / breaking),
severity 0-10, and which topics moved. Other contracts can read it, e.g. pause a service or
require re-consent when `has_material_change_since(policy_id, index)` returns true.
