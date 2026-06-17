"""Portfolio scheduler: active worker slots, priorities, wait-time, and aging.

Enforces the active-slot cap across all projects, FIFO scheduling with manual
priority override, wait-time instrumentation, and aging promotion for starved tasks.
"""
