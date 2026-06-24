#!/usr/bin/env python3
"""CSPR.cloud auth proxy — forwards RPC calls with your access token."""
import os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

CSPR_CLOUD_URL = "https://node.testnet.cspr.cloud/rpc"
ACCESS_TOKEN = os.environ.get("CSPR_CLOUD_TOKEN") or "019ea917-7049-7319-aa18-a8110aa3952f"


class ProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            resp = requests.post(
                CSPR_CLOUD_URL,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": ACCESS_TOKEN,
                },
                timeout=60,
            )
            self.send_response(resp.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.content)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, fmt, *args):
        print(f"[cspr-proxy] {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 17777
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)
    print(f"CSPR.cloud proxy running on http://127.0.0.1:{port}")
    print(f"Forwarding -> {CSPR_CLOUD_URL}")
    server.serve_forever()
