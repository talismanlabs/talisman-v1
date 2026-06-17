"""LangGraph spiral workflow mechanics.

Owns the gated project spiral: state schema, graph nodes, checkpoints, interrupts,
and resume. May import ``domain`` and ``ports``; must not import concrete adapters
or workers. Per the guardrails, LangGraph owns workflow *mechanics* only — policy,
security, review, and cost decisions live elsewhere.
"""
