"""Idempotent launcher for the GBT holographic panel.

The launcher first probes the existing local bridge. If the same panel is
already serving, it reuses that process instead of starting a duplicate.
"""
from __future__ import annotations

import argparse
import json
import threading
import urllib.error
import urllib.request
import webbrowser

from panel_server import HoloBridge, create_server


def _panel_ready(host: str, port: int, timeout: float = 0.8) -> bool:
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/api/state",
            timeout=timeout,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return bool(isinstance(payload, dict) and payload.get("ok"))
    except (OSError, ValueError, urllib.error.URLError):
        return False


def _open_browser(url: str, delay: float = 0.7) -> None:
    timer = threading.Timer(delay, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Start or reuse the GBT holographic panel")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-codex", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)

    host = args.host
    port = int(args.port)
    url = f"http://{host}:{port}/"
    if _panel_ready(host, port):
        print(f"GBT panel already running: {url}")
        if not args.no_browser:
            _open_browser(url, delay=0.1)
        return 0

    bridge = HoloBridge()
    if not args.no_codex:
        bridge.start(wait_seconds=0.0)

    server = None
    last_error = None
    for candidate in range(port, port + 10):
        try:
            server = create_server(host, candidate, bridge)
            port = int(server.server_port)
            break
        except OSError as exc:
            last_error = exc
    if server is None:
        bridge.stop()
        print(f"Unable to start GBT panel: {last_error}")
        return 1

    url = f"http://{host}:{port}/"
    print(f"GBT holographic panel: {url}")
    if not args.no_browser:
        _open_browser(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
