"""
Local Web Chatbot Studio for Vibe Coding.
Provides a modern split-screen interface (Chat + Code Preview) on http://localhost:8000.
"""

import os
import json
import asyncio
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from ace.config import settings
from ace.agents.supervisor import SupervisorAgent
from ace.tools.file_ops import list_files, read_file
from ace.tools.git_ops import GitManager

STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACE Vibe Coding Studio</title>
    <style>
        :root {
            --bg-main: #0a0d12;
            --bg-panel: #11151c;
            --bg-card: #191f2b;
            --border: #273142;
            --text-main: #e6edf3;
            --text-dim: #8b949e;
            --accent: #58a6ff;
            --accent-glow: rgba(88, 166, 255, 0.25);
            --emerald: #3fb950;
            --purple: #bc8cff;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            overflow: hidden;
        }
        header {
            height: 52px;
            background-color: var(--bg-panel);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            font-size: 16px;
        }
        .brand-badge {
            background: linear-gradient(135deg, #58a6ff, #bc8cff);
            color: #fff;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }
        .status-pill {
            background-color: rgba(63, 185, 80, 0.15);
            color: var(--emerald);
            border: 1px solid rgba(63, 185, 80, 0.3);
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .status-dot { width: 8px; height: 8px; background-color: var(--emerald); border-radius: 50%; }

        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        /* Left: Chat Pane */
        .chat-pane {
            width: 45%;
            display: flex;
            flex-direction: column;
            border-right: 1px solid var(--border);
            background-color: var(--bg-panel);
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .msg {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 14px;
            animation: fadeIn 0.2s ease-in-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .msg-user {
            align-self: flex-end;
            background-color: #1f6feb;
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .msg-ai {
            align-self: flex-start;
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }
        .chips-container {
            display: flex;
            gap: 8px;
            padding: 8px 20px;
            overflow-x: auto;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .chip {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .chip:hover { border-color: var(--accent); color: var(--text-main); }
        .chat-input-area {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 10px;
            background-color: var(--bg-panel);
        }
        textarea {
            flex: 1;
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-main);
            padding: 12px;
            font-size: 14px;
            resize: none;
            height: 52px;
            outline: none;
            font-family: inherit;
        }
        textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-glow); }
        button.btn-send {
            background: linear-gradient(135deg, #238636, #2ea043);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0 20px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button.btn-send:hover { opacity: 0.9; }
        button.btn-send:disabled { opacity: 0.5; cursor: not-allowed; }

        /* Right: Code & File Preview */
        .preview-pane {
            width: 55%;
            display: flex;
            flex-direction: column;
            background-color: var(--bg-main);
        }
        .tabs {
            height: 42px;
            display: flex;
            border-bottom: 1px solid var(--border);
            background-color: var(--bg-panel);
        }
        .tab {
            padding: 0 16px;
            display: flex;
            align-items: center;
            cursor: pointer;
            font-size: 13px;
            color: var(--text-dim);
            border-right: 1px solid var(--border);
        }
        .tab.active {
            color: var(--text-main);
            background-color: var(--bg-main);
            font-weight: 600;
            border-bottom: 2px solid var(--accent);
        }
        .preview-content {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        .file-tree {
            width: 200px;
            border-right: 1px solid var(--border);
            padding: 12px;
            overflow-y: auto;
            font-size: 13px;
        }
        .file-item {
            padding: 6px 8px;
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-dim);
            text-overflow: ellipsis;
            overflow: hidden;
            white-space: nowrap;
        }
        .file-item:hover, .file-item.selected {
            background-color: var(--bg-card);
            color: var(--text-main);
        }
        .code-view {
            flex: 1;
            padding: 16px;
            overflow: auto;
            font-family: "SF Mono", Menlo, Monaco, Consolas, monospace;
            font-size: 13px;
            line-height: 1.5;
            background-color: #05070a;
            color: #d1d7e0;
            white-space: pre;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span>🤖 ACE Studio</span>
            <span class="brand-badge">VIBE CODING</span>
        </div>
        <div class="status-pill">
            <div class="status-dot"></div>
            <span>Dual Gemini Flash Active &bull; 3,000 req/day</span>
        </div>
    </header>

    <div class="main-container">
        <!-- Chat Pane -->
        <div class="chat-pane">
            <div class="chat-messages" id="chat-box">
                <div class="msg msg-ai">
                    👋 <b>Selamat datang di ACE Vibe Coding Studio!</b><br>
                    Tuliskan ide aplikasi atau fitur yang ingin Anda bangun dalam bahasa santai (ID/EN). ACE akan merancang, mengoding, dan menguji semuanya secara otomatis.
                </div>
            </div>

            <div class="chips-container">
                <div class="chip" onclick="usePrompt('Buatkan halaman portfolio estetik dengan tema dark mode dan Tailwind CSS')">✨ Portfolio Dark Mode</div>
                <div class="chip" onclick="usePrompt('Scaffold aplikasi mobile Flutter + Rust FFI')">📱 Mobile Flutter + Rust</div>
                <div class="chip" onclick="usePrompt('Buat REST API autentikasi JWT di FastAPI')">⚡ FastAPI Auth API</div>
                <div class="chip" onclick="usePrompt('Tambahkan unit test coverage 100% untuk modul yang ada')">🧪 Add Unit Tests</div>
            </div>

            <div class="chat-input-area">
                <textarea id="user-input" placeholder="Ketik instruksi vibe coding Anda di sini (Enter untuk kirim)..." onkeydown="handleKey(event)"></textarea>
                <button class="btn-send" id="btn-send" onclick="sendPrompt()">Send</button>
            </div>
        </div>

        <!-- Preview Pane -->
        <div class="preview-pane">
            <div class="tabs">
                <div class="tab active" id="tab-code" onclick="switchTab('code')">📄 File & Code Viewer</div>
                <div class="tab" id="tab-diff" onclick="switchTab('diff')">📝 Live Git Diff</div>
            </div>
            <div class="preview-content">
                <div class="file-tree" id="file-list">
                    <div style="color: var(--text-dim); padding: 8px;">Loading files...</div>
                </div>
                <div class="code-view" id="code-display">// Pilih file di panel kiri untuk melihat isi kode</div>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'code';

        function usePrompt(text) {
            document.getElementById('user-input').value = text;
            document.getElementById('user-input').focus();
        }

        function handleKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPrompt();
            }
        }

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('tab-code').classList.toggle('active', tab === 'code');
            document.getElementById('tab-diff').classList.toggle('active', tab === 'diff');
            if (tab === 'diff') {
                loadDiff();
            }
        }

        async function loadFiles() {
            try {
                const res = await fetch('/api/files');
                const data = await res.json();
                const container = document.getElementById('file-list');
                if (data.files && data.files.length > 0) {
                    container.innerHTML = data.files.map(f => `
                        <div class="file-item" onclick="viewFile('${f}')" title="${f}">📄 ${f}</div>
                    `).join('');
                } else {
                    container.innerHTML = '<div style="color: var(--text-dim); padding: 8px;">No files yet.</div>';
                }
            } catch (e) {
                console.error(e);
            }
        }

        async function viewFile(filePath) {
            try {
                const res = await fetch(`/api/file?path=${encodeURIComponent(filePath)}`);
                const data = await res.json();
                document.getElementById('code-display').innerText = data.content || '// Empty file';
            } catch (e) {
                console.error(e);
            }
        }

        async function loadDiff() {
            try {
                const res = await fetch('/api/diff');
                const data = await res.json();
                document.getElementById('code-display').innerText = data.diff || '// No uncommitted git diffs.';
            } catch (e) {
                console.error(e);
            }
        }

        async function sendPrompt() {
            const input = document.getElementById('user-input');
            const prompt = input.value.trim();
            if (!prompt) return;

            const chatBox = document.getElementById('chat-box');
            chatBox.innerHTML += `<div class="msg msg-user">${prompt}</div>`;
            input.value = '';
            
            const btn = document.getElementById('btn-send');
            btn.disabled = true;
            btn.innerText = 'Working...';

            const thinkingMsg = document.createElement('div');
            thinkingMsg.className = 'msg msg-ai';
            thinkingMsg.innerHTML = '🤖 <i>ACE sedang menganalisis, mengoding, dan menguji...</i>';
            chatBox.appendChild(thinkingMsg);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const result = await res.json();

                thinkingMsg.innerHTML = `
                    <b>✅ Task Selesai!</b><br>
                    • Status: <span style="color: var(--emerald);">${result.status}</span><br>
                    • Branch: <code>${result.branch || 'main'}</code><br>
                    • File Dimodifikasi: <b>${result.files_modified ? result.files_modified.length : 0}</b> file
                `;
                loadFiles();
                if (currentTab === 'diff') loadDiff();
            } catch (e) {
                thinkingMsg.innerHTML = `❌ Error: ${e.message}`;
            } finally {
                btn.disabled = false;
                btn.innerText = 'Send';
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        loadFiles();
    </script>
</body>
</html>
"""


class StudioHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request handler for Studio UI and API endpoints."""

    supervisor = SupervisorAgent()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/studio"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(STUDIO_HTML.encode("utf-8"))
            return

        if parsed.path == "/api/files":
            files = list_files(Path.cwd())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"files": files}).encode("utf-8"))
            return

        if parsed.path == "/api/file":
            qs = parse_qs(parsed.query)
            file_path = qs.get("path", [""])[0]
            content = ""
            if file_path:
                try:
                    content = read_file(file_path, base_dir=Path.cwd())
                except Exception as e:
                    content = f"Error reading file: {e}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"file_path": file_path, "content": content}).encode("utf-8"))
            return

        if parsed.path == "/api/diff":
            git_mgr = GitManager(Path.cwd())
            diff = git_mgr.get_diff()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"diff": diff}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            payload_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(payload_bytes.decode("utf-8"))
                prompt = data.get("prompt", "")
                result = asyncio.run(self.supervisor.run_task(prompt=prompt, locale="id"))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def launch_studio(port: int = 8000) -> None:
    """Launch the Web Studio HTTP Server."""
    server = HTTPServer(("0.0.0.0", port), StudioHTTPHandler)
    print(f"\n🎨 ACE Vibe Coding Studio running at: http://localhost:{port}")
    print("👉 Buka link di atas pada browser untuk mulai coding secara visual!\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Studio server stopped.")
