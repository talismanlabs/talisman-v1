"""Integration tests for the egress gatekeeper proxy (slice S16.04, ADR-0006).

These spin up a real proxy on a loopback socket and drive it with a real client socket,
so they prove the enforcement end-to-end rather than mocking it.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from talisman_core.adapters.egress_proxy import EgressProxy


def test_proxy_can_bind_all_interfaces_for_the_gateway() -> None:
    """The proxy can bind 0.0.0.0 so workers reach it from the sealed network (S16.19; ADR-0009)."""
    with EgressProxy(host="0.0.0.0", port=0) as proxy:
        assert proxy.address[0] == "0.0.0.0"
        assert proxy.proxy_url.startswith("http://0.0.0.0:")


def _read_response_head(sock: socket.socket) -> str:
    """Read up to the blank-line terminator and return the HTTP status line."""
    buffer = b""
    while b"\r\n\r\n" not in buffer:
        chunk = sock.recv(1024)
        if not chunk:
            break
        buffer += chunk
    return buffer.split(b"\r\n", 1)[0].decode("latin-1")


@contextmanager
def _origin_server() -> Iterator[tuple[str, int]]:
    """A tiny TCP origin: on connect, read one chunk and reply ``ORIGIN-OK``."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()

    def serve() -> None:
        try:
            conn, _ = server.accept()
            with conn:
                conn.recv(1024)
                conn.sendall(b"ORIGIN-OK")
        except OSError:
            pass

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield host, port
    finally:
        server.close()
        thread.join(timeout=5)


def test_proxy_tunnels_to_an_allowed_target() -> None:
    """An allowlisted CONNECT target is tunnelled end-to-end (both directions)."""
    with (
        _origin_server() as (origin_host, origin_port),
        EgressProxy(is_allowed=lambda host: True) as proxy,
    ):
        phost, pport = proxy.address
        with socket.create_connection((phost, pport), timeout=5) as client:
            client.sendall(
                f"CONNECT {origin_host}:{origin_port} HTTP/1.1\r\n\r\n".encode("latin-1")
            )
            assert "200 Connection Established" in _read_response_head(client)
            client.sendall(b"hi")
            assert client.recv(1024) == b"ORIGIN-OK"


def test_proxy_denies_a_non_allowlisted_host() -> None:
    """A host outside the real egress allowlist is refused with 403 (fail-closed)."""
    with EgressProxy() as proxy:  # real security.egress policy
        phost, pport = proxy.address
        with socket.create_connection((phost, pport), timeout=5) as client:
            client.sendall(b"CONNECT evil.example.com:443 HTTP/1.1\r\n\r\n")
            assert "403 Forbidden" in _read_response_head(client)


def test_proxy_refuses_non_connect_requests() -> None:
    """Non-CONNECT (plain-HTTP proxying) is intentionally refused — default-deny."""
    with EgressProxy(is_allowed=lambda host: True) as proxy:
        phost, pport = proxy.address
        with socket.create_connection((phost, pport), timeout=5) as client:
            client.sendall(
                b"GET http://evil.example.com/ HTTP/1.1\r\nHost: evil.example.com\r\n\r\n"
            )
            assert "501 Not Implemented" in _read_response_head(client)
