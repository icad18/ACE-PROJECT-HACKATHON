"""
GitHub REST API Client.
Uses Python standard library urllib for zero-dependency HTTP communication.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from ace.config import settings


class GitHubClient:
    """Interacts with GitHub REST API v3 using Personal Access Token or App Token."""

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token or settings.github_token
        self.base_url = base_url.rstrip("/")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute authenticated HTTP request to GitHub."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        req_headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Autonomous-Code-Engineer-ACE",
        }
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30.0) as response:
                resp_data = response.read().decode("utf-8")
                if resp_data:
                    return json.loads(resp_data)
                return {"status": response.status}
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API Error [{e.code}]: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Network error connecting to GitHub: {e}")

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head_branch: str,
        base_branch: str = "main",
        body: str = "",
        draft: bool = False
    ) -> Dict[str, Any]:
        """Create a new Pull Request."""
        payload = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "draft": draft
        }
        return self._request("POST", f"repos/{owner}/{repo}/pulls", data=payload)

    def post_issue_comment(self, owner: str, repo: str, issue_number: int, comment: str) -> Dict[str, Any]:
        """Post a comment to an issue or pull request."""
        payload = {"body": comment}
        return self._request("POST", f"repos/{owner}/{repo}/issues/{issue_number}/comments", data=payload)

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetch issue details and body."""
        return self._request("GET", f"repos/{owner}/{repo}/issues/{issue_number}")

    def get_pull_request_files(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """List files changed in a Pull Request."""
        return self._request("GET", f"repos/{owner}/{repo}/pulls/{pull_number}/files")
