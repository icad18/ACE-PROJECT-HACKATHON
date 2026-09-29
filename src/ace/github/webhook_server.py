"""
Lightweight Webhook Listener for GitHub events with HMAC-SHA256 security.
"""

import hmac
import hashlib
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Callable
from ace.github.slash_commands import SlashCommandProcessor, CommandType
from ace.github.api import GitHubClient


def verify_signature(secret: str, payload_bytes: bytes, signature_header: str) -> bool:
    """Verify GitHub HMAC-SHA256 webhook signature."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_hash = signature_header[7:]
    mac = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), expected_hash)


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for incoming GitHub webhook payloads."""

    webhook_secret: Optional[str] = None
    event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        payload_bytes = self.rfile.read(content_length)

        # Signature verification if secret configured
        if self.webhook_secret:
            sig_header = self.headers.get("X-Hub-Signature-256", "")
            if not verify_signature(self.webhook_secret, payload_bytes, sig_header):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid webhook signature")
                return

        event_type = self.headers.get("X-GitHub-Event", "ping")

        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # Process standard events
        self._handle_event(event_type, payload)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "accepted", "event": event_type}).encode("utf-8"))

    def _handle_event(self, event_type: str, payload: Dict[str, Any]):
        """Route GitHub events to appropriate handler."""
        if event_type == "issue_comment" and payload.get("action") == "created":
            comment_body = payload.get("comment", {}).get("body", "")
            sender = payload.get("sender", {}).get("login", "")
            issue_number = payload.get("issue", {}).get("number", 0)
            repo = payload.get("repository", {})
            owner = repo.get("owner", {}).get("login", "")
            repo_name = repo.get("name", "")

            parsed = SlashCommandProcessor.parse_comment(comment_body, sender=sender, issue_number=issue_number)
            if parsed and owner and repo_name:
                resp_text = SlashCommandProcessor.generate_response(parsed)
                # Post automated response
                try:
                    gh = GitHubClient()
                    gh.post_issue_comment(owner=owner, repo=repo_name, issue_number=issue_number, comment=resp_text)
                except Exception as e:
                    print(f"[Webhook Error] Failed to post reply: {e}")

        if self.event_callback:
            try:
                self.event_callback(event_type, payload)
            except Exception as e:
                print(f"[Webhook Callback Error]: {e}")

    def log_message(self, format, *args):
        # Quiet standard HTTP server logs
        pass


def start_webhook_server(
    port: int = 8080,
    secret: Optional[str] = None,
    callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
) -> HTTPServer:
    """Start local webhook server listener."""
    WebhookHandler.webhook_secret = secret
    WebhookHandler.event_callback = callback
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    return server
