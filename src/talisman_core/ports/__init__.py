"""Typed interfaces (ports) for external capabilities.

Ports are ``typing.Protocol`` contracts for workers, approval, state, gateway,
memory, and notifications. They declare *what* the core needs without binding it to
*how* it is provided. Ports may define interfaces but must not import concrete
adapters.
"""
