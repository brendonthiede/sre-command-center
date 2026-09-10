"""One-shot OAuth: serve the redirect on localhost:8790, exchange the code, write SLACK_USER_TOKEN to .env.

Run once: `uv run python slack-app/oauth.py`, open the printed URL, click Allow.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scc.config import secret  # noqa: E402  (loads .env)

SCOPES = "channels:history,channels:read,groups:history,groups:read"
REDIRECT = "http://localhost:8790/"
CLIENT_ID, CLIENT_SECRET = secret("SLACK_CLIENT_ID"), secret("SLACK_CLIENT_SECRET")
print("Open this URL and click Allow:\n"
      f"https://slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&user_scope={SCOPES}"
      f"&redirect_uri={urllib.parse.quote(REDIRECT, safe='')}\n", flush=True)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("code", [None])[0]
        if not code:
            self.send_response(400); self.end_headers(); self.wfile.write(b"no code"); return
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://slack.com/api/oauth.v2.access",
            data=urllib.parse.urlencode({"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                                         "code": code, "redirect_uri": REDIRECT}).encode())))
        if not r.get("ok"):
            self.send_response(500); self.end_headers(); self.wfile.write(json.dumps(r).encode())
            print("exchange failed:", r, flush=True); return
        token = r["authed_user"]["access_token"]
        env = ROOT / ".env"
        text = re.sub(r"^SLACK_USER_TOKEN=.*$", f"SLACK_USER_TOKEN={token}", env.read_text(), flags=re.M)
        if "SLACK_USER_TOKEN=" not in text:
            text += f"\nSLACK_USER_TOKEN={token}\n"
        env.write_text(text)
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Slack user token saved to .env. You can close this tab.")
        print("saved SLACK_USER_TOKEN with scopes:", r["authed_user"].get("scope"), flush=True)
        self.server.done = True

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8790), H)
srv.done = False
while not srv.done:
    srv.handle_request()
