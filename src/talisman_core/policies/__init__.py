"""Policy layer: tiering, review routing, escalation, and budget decisions.

Encodes TalisMan's decisions — workflow tier selection, cross/same-family review
routing, escalation thresholds, and budget enforcement rules. Policies operate on
domain objects and simple value types and must not call external systems directly.
"""
