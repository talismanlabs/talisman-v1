"""Egress gatekeeper proxy (slice S16.04; decision ADR-0006).

A local forward proxy that is the egress allowlist's *decision point* on real outbound
connections. Given a connection it permits an HTTPS ``CONNECT`` tunnel only to an
allowlisted host (``security.egress``) and returns ``403`` for everything else. Because it
sees only the CONNECT target host, not the TLS-encrypted payload, it controls *where*
traffic may go without inspecting it. Making it the *only* route to the network — so a worker
cannot bypass it — requires OS-level containment, NOT ``HTTPS_PROXY`` alone (which is
cooperative); see ADR-0006 ("Enforcement is two parts").

Fail-closed: non-``CONNECT`` requests are refused (``501``) and non-allowlisted hosts are
refused (``403``). Binds to loopback by default. The allow predicate is injectable so the
enforcement mechanism is testable independently of the specific allowlist.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable
from socketserver import StreamRequestHandler, ThreadingTCPServer
from typing import cast

from talisman_core.security.egress import is_allowed as policy_is_allowed

# Predicate deciding whether a destination host may be reached.
AllowPredicate = Callable[[str], bool]

_MAX_LINE = 65536
_TUNNEL_CHUNK = 65536
_CONNECT_TIMEOUT = 10.0


class _EgressProxyServer(ThreadingTCPServer):
    """Threading TCP server carrying the injected egress allow predicate."""

    daemon_threads = True
    allow_reuse_address = True
    is_allowed: AllowPredicate


class _EgressProxyHandler(StreamRequestHandler):
    """Enforce the egress allowlist for one proxied connection."""

    def handle(self) -> None:
        server = cast("_EgressProxyServer", self.server)
        request_line = self.rfile.readline(_MAX_LINE).decode("latin-1").strip()
        self._drain_headers()

        parts = request_line.split(" ")
        if len(parts) < 2 or parts[0].upper() != "CONNECT":
            self._respond("501 Not Implemented")
            return

        host, port = self._parse_authority(parts[1])
        if host is None:
            self._respond("400 Bad Request")
            return
        if not server.is_allowed(host):
            self._respond("403 Forbidden")
            return

        try:
            upstream = socket.create_connection((host, port), timeout=_CONNECT_TIMEOUT)
        except OSError:
            self._respond("502 Bad Gateway")
            return

        self._respond("200 Connection Established")
        with upstream:
            self._tunnel(self.connection, upstream)

    def _drain_headers(self) -> None:
        """Read and discard request headers up to the terminating blank line."""
        while True:
            line = self.rfile.readline(_MAX_LINE)
            if line in (b"\r\n", b"\n", b""):
                return

    def _parse_authority(self, authority: str) -> tuple[str | None, int]:
        """Split a CONNECT ``host:port`` authority; default port 443, fail closed on junk."""
        host, _, port_str = authority.rpartition(":")
        if not host:  # no colon present — authority was a bare host
            host, port_str = authority, ""
        host = host.strip("[]")  # IPv6 literal brackets
        if not host:
            return None, 0
        try:
            port = int(port_str) if port_str else 443
        except ValueError:
            return None, 0
        return host, port

    def _respond(self, status: str) -> None:
        self.wfile.write(f"HTTP/1.1 {status}\r\n\r\n".encode("latin-1"))
        self.wfile.flush()

    def _tunnel(self, client: socket.socket, upstream: socket.socket) -> None:
        """Blindly pipe bytes both ways until either side closes."""

        def pipe(src: socket.socket, dst: socket.socket) -> None:
            try:
                while True:
                    chunk = src.recv(_TUNNEL_CHUNK)
                    if not chunk:
                        break
                    dst.sendall(chunk)
            except OSError:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except OSError:
                    pass

        upstream_to_client = threading.Thread(target=pipe, args=(upstream, client), daemon=True)
        upstream_to_client.start()
        pipe(client, upstream)
        upstream_to_client.join(timeout=_CONNECT_TIMEOUT)


class EgressProxy:
    """A running egress gatekeeper proxy bound to a local address.

    Usage::

        with EgressProxy() as proxy:
            os.environ["HTTPS_PROXY"] = proxy.proxy_url
            ...  # all CONNECTs now enforced against the egress allowlist
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        is_allowed: AllowPredicate = policy_is_allowed,
    ) -> None:
        self._server = _EgressProxyServer((host, port), _EgressProxyHandler)
        self._server.is_allowed = is_allowed
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        """The bound ``(host, port)`` (port is concrete even when constructed with 0)."""
        host, port = cast("tuple[str, int]", self._server.server_address)
        return host, port

    @property
    def proxy_url(self) -> str:
        """The ``http://host:port`` URL to set as HTTPS_PROXY/HTTP_PROXY."""
        host, port = self.address
        return f"http://{host}:{port}"

    def start(self) -> None:
        """Serve in a background daemon thread."""
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop serving and release the socket."""
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def __enter__(self) -> EgressProxy:
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()
