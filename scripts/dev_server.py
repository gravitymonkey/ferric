#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import mimetypes
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, parse, request


ROOT = Path.cwd().resolve()
PORT = int(os.environ.get("PORT", "8080"))
BACKEND_ORIGIN = os.environ.get("BACKEND_ORIGIN", "http://127.0.0.1:8000").rstrip("/")
LOG_PATH = Path(os.environ.get("FERRIC_FRONTEND_LOG_PATH", str(ROOT / "backend" / "logs" / "frontend.log"))).resolve()
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("ferric.frontend")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/vnd.apple.mpegurl", ".m3u8")
mimetypes.add_type("video/mp2t", ".ts")
mimetypes.add_type("audio/mpeg", ".mp3")


class DevHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        self._handle()

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle(send_body=False)

    def do_POST(self) -> None:  # noqa: N802
        self._handle()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle()

    def _handle(self, send_body: bool = True) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self._proxy_to_backend(send_body=send_body)
            return

        if self.command not in {"GET", "HEAD"}:
            self.send_error(405, "Method Not Allowed")
            return
        self._serve_static(send_body=send_body)

    def _proxy_to_backend(self, send_body: bool) -> None:
        upstream = f"{BACKEND_ORIGIN}{self.path}"
        upstream_path = parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        req = request.Request(upstream, data=body, method=self.command, headers=headers)

        try:
            with request.urlopen(req, timeout=20) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    lower = key.lower()
                    if lower in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(key, value)
                self.send_header("Connection", "close")
                self.end_headers()
                if send_body:
                    self.wfile.write(payload)
                logger.info("proxy method=%s path=%s status=%s upstream=%s", self.command, upstream_path, resp.status, BACKEND_ORIGIN)
        except error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                lower = key.lower()
                if lower in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()
            if send_body:
                self.wfile.write(payload)
            logger.info("proxy method=%s path=%s status=%s upstream=%s", self.command, upstream_path, exc.code, BACKEND_ORIGIN)
        except Exception:
            payload = json.dumps(
                {
                    "error": "backend_unreachable",
                    "message": f"Could not reach backend at {BACKEND_ORIGIN}",
                }
            ).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            if send_body:
                self.wfile.write(payload)
            logger.exception("proxy_error method=%s path=%s upstream=%s", self.command, upstream_path, BACKEND_ORIGIN)

    def _serve_static(self, send_body: bool) -> None:
        parsed = parse.urlparse(self.path)
        req_path = parsed.path or "/"
        if req_path == "/":
            req_path = "/public/index.html"

        target = (ROOT / req_path.lstrip("/")).resolve()
        if not str(target).startswith(str(ROOT)):
            self.send_error(403, "Forbidden")
            return
        if not target.exists() or target.is_dir():
            self.send_error(404, "Not Found")
            return

        ctype, _ = mimetypes.guess_type(str(target))
        payload_size = target.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", ctype or "application/octet-stream")
        self.send_header("Content-Length", str(payload_size))
        self.send_header("Connection", "close")
        self.end_headers()
        if send_body:
            with target.open("rb") as fh:
                shutil.copyfileobj(fh, self.wfile)
        logger.info("static method=%s path=%s status=200", self.command, req_path)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    server = ThreadingHTTPServer(("", PORT), DevHandler)
    print(f"Ferric python dev server running on http://localhost:{PORT}/public/index.html")
    logger.info("frontend_server_start port=%s root=%s", PORT, ROOT)
    server.serve_forever()


if __name__ == "__main__":
    main()
