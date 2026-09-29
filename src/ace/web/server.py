"""
Full Stack Web Control Center for ACE (Autonomous Code Engineer).
Provides visual Setup, Live Quota & Token Monitoring, Trajectory Progress Bar,
Persistent Conversational Web Studio with Interactive Code Inspector, Live Preview,
and 1-Click Copy & Edit on user chat bubbles.
"""

import os
import json
import asyncio
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List

from ace.config import settings, load_dotenv
from ace.db.connection import get_db, init_db
from ace.llm.quota import QuotaTracker
from ace.llm.router import LLMRouter, TaskComplexity
from ace.agents.supervisor import SupervisorAgent
from ace.tools.file_ops import list_files, read_file
from ace.tools.git_ops import GitManager
from ace.web.config_manager import ConfigManager

CONTROL_CENTER_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACE Control Center & Vibe Studio</title>
    <style>
        /* ================= THEME DEFINITIONS ================= */
        :root {
            --bg-body: #090d16;
            --bg-sidebar: #0f1523;
            --bg-card: #141c2e;
            --bg-input: #1b253b;
            --border: #233047;
            --border-hover: #3b82f6;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-gradient: linear-gradient(135deg, #38bdf8, #818cf8);
            --emerald: #10b981;
            --amber: #f59e0b;
            --rose: #f43f5e;
            --code-bg: #050811;
        }

        body.theme-oled {
            --bg-body: #000000;
            --bg-sidebar: #0a0a0a;
            --bg-card: #121212;
            --bg-input: #1a1a1a;
            --border: #262626;
            --border-hover: #a855f7;
            --text-main: #fafafa;
            --text-muted: #a1a1aa;
            --accent: #a855f7;
            --accent-gradient: linear-gradient(135deg, #a855f7, #ec4899);
            --emerald: #22c55e;
            --amber: #fbbf24;
            --rose: #fb7185;
            --code-bg: #000000;
        }

        body.theme-clean {
            --bg-body: #f8fafc;
            --bg-sidebar: #ffffff;
            --bg-card: #ffffff;
            --bg-input: #f1f5f9;
            --border: #e2e8f0;
            --border-hover: #0284c7;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --accent: #0284c7;
            --accent-gradient: linear-gradient(135deg, #0284c7, #6366f1);
            --emerald: #059669;
            --amber: #d97706;
            --rose: #e11d48;
            --code-bg: #f8fafc;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            overflow: hidden;
            transition: background-color 0.2s, color 0.2s;
        }

        /* Sidebar */
        aside {
            width: 260px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px 16px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }
        .brand-icon {
            font-size: 22px;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        .brand-text h2 { font-size: 15px; font-weight: 700; color: var(--text-main); }
        .brand-text span { font-size: 11px; color: var(--text-muted); }

        nav { display: flex; flex-direction: column; gap: 6px; flex: 1; }
        .nav-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid transparent;
            background: transparent;
            color: var(--text-muted);
            font-size: 13.5px;
            font-weight: 500;
            cursor: pointer;
            text-align: left;
            transition: all 0.15s ease-in-out;
        }
        .nav-btn:hover { background-color: var(--bg-card); color: var(--text-main); }
        .nav-btn.active {
            background-color: var(--bg-card);
            border-color: var(--border);
            color: var(--accent);
            font-weight: 600;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .theme-box {
            padding-top: 16px;
            border-top: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .theme-box label { font-size: 11.5px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
        .theme-select {
            background-color: var(--bg-card);
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 8px 10px;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
            cursor: pointer;
        }

        /* Main Container */
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            background-color: var(--bg-body);
        }
        header {
            height: 60px;
            background-color: var(--bg-sidebar);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 28px;
        }
        .header-title h1 { font-size: 17px; font-weight: 700; }
        .header-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12.5px;
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            padding: 5px 14px;
            border-radius: 20px;
        }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background-color: var(--emerald); }

        .content-section { display: none; padding: 28px; }
        .content-section.active { display: block; animation: fadeIn 0.2s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        /* Grid & Cards */
        .grid-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .card-header { display: flex; justify-content: space-between; align-items: center; }
        .card-title { font-size: 14px; font-weight: 600; color: var(--text-muted); }
        .card-value { font-size: 26px; font-weight: 700; color: var(--text-main); }
        
        /* Progress Bars */
        .progress-container { width: 100%; display: flex; flex-direction: column; gap: 6px; }
        .progress-bar-bg {
            height: 10px;
            background-color: var(--bg-input);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }
        .progress-bar-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 6px;
            transition: width 0.4s ease;
        }
        .progress-labels { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); }

        /* Trajectory Stepper */
        .trajectory-stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            margin: 20px 0;
            padding: 0 10px;
        }
        .trajectory-stepper::before {
            content: "";
            position: absolute;
            top: 50%;
            left: 20px;
            right: 20px;
            height: 4px;
            background-color: var(--border);
            transform: translateY(-50%);
            z-index: 1;
        }
        .step-node {
            position: relative;
            z-index: 2;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .step-circle {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: var(--bg-card);
            border: 2px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 700;
            color: var(--text-muted);
            transition: all 0.3s;
        }
        .step-node.completed .step-circle {
            background-color: var(--emerald);
            border-color: var(--emerald);
            color: #fff;
        }
        .step-node.active .step-circle {
            border-color: var(--accent);
            color: var(--accent);
            box-shadow: 0 0 12px var(--accent);
        }
        .step-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
        .step-node.completed .step-label, .step-node.active .step-label { color: var(--text-main); font-weight: 600; }

        /* Forms */
        .form-group { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
        .form-group label { font-size: 13px; font-weight: 600; color: var(--text-main); }
        .form-group span.desc { font-size: 12px; color: var(--text-muted); }
        .input-row { display: flex; gap: 10px; }
        input[type="text"], input[type="password"] {
            flex: 1;
            background-color: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-main);
            padding: 10px 14px;
            font-size: 13.5px;
            outline: none;
            font-family: inherit;
        }
        input:focus { border-color: var(--border-hover); }
        .btn {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .btn-primary { background: var(--accent-gradient); color: #fff; }
        .btn-primary:hover { opacity: 0.9; }
        .btn-secondary { background-color: var(--bg-input); border-color: var(--border); color: var(--text-main); }
        .btn-secondary:hover { background-color: var(--border); }
        .btn-test { background-color: rgba(56, 189, 248, 0.15); color: var(--accent); border-color: rgba(56, 189, 248, 0.3); }

        /* Tables */
        table { width: 100%; border-collapse: collapse; margin-top: 14px; }
        th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13.5px; }
        th { color: var(--text-muted); font-weight: 600; }
        .badge { padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 600; }
        .badge-success { background-color: rgba(16, 185, 129, 0.15); color: var(--emerald); }
        .badge-warning { background-color: rgba(245, 158, 11, 0.15); color: var(--amber); }

        /* Studio Split Screen */
        .studio-container {
            display: flex;
            height: calc(100vh - 120px);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            background-color: var(--bg-card);
        }
        .studio-chat { width: 45%; display: flex; flex-direction: column; border-right: 1px solid var(--border); }
        .studio-chat-header {
            height: 44px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            background-color: var(--bg-sidebar);
            font-size: 12.5px;
            font-weight: 600;
        }
        .studio-preview { width: 55%; display: flex; flex-direction: column; background-color: var(--code-bg); }
        .chat-box { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
        .chat-input { padding: 12px; border-top: 1px solid var(--border); display: flex; gap: 8px; }
        
        /* Chat bubble styling with hover copy and edit buttons */
        .chat-bubble-wrapper {
            position: relative;
            display: flex;
            flex-direction: column;
            width: 100%;
        }
        .chat-bubble-wrapper.user { align-items: flex-end; }
        .chat-bubble-wrapper.assistant { align-items: flex-start; }

        .chat-bubble {
            position: relative;
            max-width: 92%;
            padding: 12px 16px;
            border-radius: 10px;
            font-size: 13px;
            line-height: 1.6;
        }
        .chat-bubble.user { background: #2563eb; color: #fff; border-bottom-right-radius: 2px; }
        .chat-bubble.assistant { background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
        
        .bubble-action-btns {
            position: absolute;
            top: 6px;
            right: 6px;
            display: flex;
            gap: 4px;
            z-index: 5;
        }
        .bubble-btn {
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
            color: #cbd5e1;
            font-size: 11px;
            padding: 2px 7px;
            border-radius: 4px;
            cursor: pointer;
            opacity: 0.75;
            transition: all 0.15s;
        }
        .bubble-btn:hover { opacity: 1.0; background: rgba(0,0,0,0.85); color: #fff; }

        .preview-toolbar {
            height: 44px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 16px;
            background-color: var(--bg-sidebar);
        }
        .preview-tabs { display: flex; gap: 6px; }
        .preview-tab-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-muted);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }
        .preview-tab-btn.active {
            background-color: var(--bg-card);
            border-color: var(--border);
            color: var(--accent);
        }
        .code-display { flex: 1; padding: 16px; font-family: "SF Mono", monospace; font-size: 13px; color: var(--text-main); overflow: auto; white-space: pre; }
        .iframe-preview { width: 100%; height: 100%; border: none; background: #ffffff; }

        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background-color: var(--bg-card);
            border: 1px solid var(--emerald);
            color: var(--emerald);
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 13.5px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: none;
            z-index: 100;
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <aside>
        <div class="brand">
            <div class="brand-icon">⚡</div>
            <div class="brand-text">
                <h2>ACE Hub</h2>
                <span>Autonomous Control Center</span>
            </div>
        </div>

        <nav>
            <button class="nav-btn active" onclick="switchSection('setup')">⚙️ Setup & API Keys</button>
            <button class="nav-btn" onclick="switchSection('quotas')">📊 Quota & Monitoring</button>
            <button class="nav-btn" onclick="switchSection('trajectory')">🔍 Trajectory & Progress</button>
            <button class="nav-btn" onclick="switchSection('studio')">💬 Web Vibe Studio</button>
            <button class="nav-btn" onclick="switchSection('terminal')">💻 Terminal Launcher</button>
        </nav>

        <div class="theme-box">
            <label>Pilihan Tema Visual:</label>
            <select class="theme-select" id="theme-selector" onchange="changeTheme(this.value)">
                <option value="theme-linear">Linear Dark (Default)</option>
                <option value="theme-oled">OLED Cyber Minimal</option>
                <option value="theme-clean">Clean Crisp Light</option>
            </select>
        </div>
    </aside>

    <!-- Main Content -->
    <main>
        <header>
            <div class="header-title">
                <h1 id="header-text">⚙️ Setup & Konfigurasi ACE</h1>
            </div>
            <div class="header-status">
                <div class="status-dot"></div>
                <span id="system-status-pill">Dual-Key Active &bull; 3,000 req/day</span>
            </div>
        </header>

        <!-- Section 1: Setup & API Keys -->
        <section id="section-setup" class="content-section active">
            <div class="card" style="max-width: 800px; margin-bottom: 24px;">
                <h2>🔑 Konfigurasi Kunci API & Lingkungan</h2>
                <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">
                    Simpan kunci API Gemini dari <a href="https://aistudio.google.com/" target="_blank" style="color: var(--accent);">Google AI Studio</a> untuk mengaktifkan kuota 3.000 request/hari gratis.
                </p>

                <div style="margin-top: 20px;">
                    <div class="form-group">
                        <label>Gemini API Key #1 (Primary):</label>
                        <span class="desc">Kunci utama untuk eksekusi rutin (1.500 req/hari Gemini 1.5/2.5 Flash).</span>
                        <div class="input-row">
                            <input type="password" id="input-key1" placeholder="AIzaSy...">
                            <button class="btn btn-test" onclick="testKey(1)">Test Key 1</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Gemini API Key #2 (Secondary - Rotasi):</label>
                        <span class="desc">Kunci kedua untuk rotasi round-robin (+1.500 req/hari tambahan).</span>
                        <div class="input-row">
                            <input type="password" id="input-key2" placeholder="AIzaSy...">
                            <button class="btn btn-test" onclick="testKey(2)">Test Key 2</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Ollama Local Endpoint:</label>
                        <span class="desc">URL daemon Ollama lokal untuk mode offline (default: http://localhost:11434).</span>
                        <div class="input-row">
                            <input type="text" id="input-ollama" placeholder="http://localhost:11434">
                            <button class="btn btn-test" onclick="testOllama()">Ping Ollama</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>GitHub Personal Access Token (Opsional):</label>
                        <span class="desc">Diperlukan untuk otomatisasi pembukaan Pull Request & Sinkronisasi Issue.</span>
                        <input type="password" id="input-github" placeholder="ghp_...">
                    </div>

                    <div class="form-group">
                        <label>Bahasa Utama Interface:</label>
                        <select class="theme-select" id="input-locale" style="width: 200px;">
                            <option value="id">Bahasa Indonesia (Bilingual)</option>
                            <option value="en">English</option>
                        </select>
                    </div>

                    <div style="display: flex; gap: 10px; margin-top: 24px;">
                        <button class="btn btn-primary" onclick="saveConfiguration()">💾 Simpan ke .env</button>
                        <button class="btn btn-secondary" onclick="loadConfig()">🔄 Muat Ulang</button>
                    </div>
                </div>
            </div>
        </section>

        <!-- Section 2: Quotas & Monitoring -->
        <section id="section-quotas" class="content-section">
            <div class="grid-cards">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Kapasitas Gemini Flash</span>
                        <span class="badge badge-success">Dual-Key Active</span>
                    </div>
                    <div class="card-value" id="quota-flash-val">3,000 req/day</div>
                    <div class="progress-container">
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="quota-flash-bar" style="width: 0%;"></div>
                        </div>
                        <div class="progress-labels">
                            <span id="quota-flash-used">Digunakan: 0 request</span>
                            <span>Batas: 3,000 / hari (Reset 00:00 UTC)</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Kapasitas Gemini Pro</span>
                        <span class="badge badge-warning">High-Reasoning</span>
                    </div>
                    <div class="card-value" id="quota-pro-val">100 req/day</div>
                    <div class="progress-container">
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" id="quota-pro-bar" style="width: 0%; background: var(--amber);"></div>
                        </div>
                        <div class="progress-labels">
                            <span id="quota-pro-used">Digunakan: 0 request</span>
                            <span>Batas: 100 / hari</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Biaya Operasional</span>
                        <span class="badge badge-success">$0.00 / bln</span>
                    </div>
                    <div class="card-value">$0.00</div>
                    <span style="font-size: 12px; color: var(--emerald);" id="tokens-total-label">✅ 100% Free-Tier & Local SQLite Tracking</span>
                </div>
            </div>

            <div class="card">
                <h2>📊 Rincian Penggunaan API Harian Real-Time (SQLite)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Model / Provider</th>
                            <th>Key ID</th>
                            <th>Status</th>
                            <th>Request Terpakai</th>
                            <th>Token Terpakai</th>
                            <th>Limit Harian</th>
                        </tr>
                    </thead>
                    <tbody id="quota-table-body">
                        <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Memuat data kuota...</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Section 3: Trajectory & Progress Tracking -->
        <section id="section-trajectory" class="content-section">
            <div class="card" style="margin-bottom: 24px;">
                <h2>🚀 Live Project Trajectory & Pipeline Stepper</h2>
                <p style="color: var(--text-muted); font-size: 13px;">Pelacakan tahapan otonom pengembangan software secara visual.</p>
                
                <div class="trajectory-stepper">
                    <div class="step-node completed">
                        <div class="step-circle">1</div>
                        <div class="step-label">Supervisor</div>
                    </div>
                    <div class="step-node completed">
                        <div class="step-circle">2</div>
                        <div class="step-label">Planner (AST)</div>
                    </div>
                    <div class="step-node completed">
                        <div class="step-circle">3</div>
                        <div class="step-label">Coder (Diffs)</div>
                    </div>
                    <div class="step-node completed">
                        <div class="step-circle">4</div>
                        <div class="step-label">Tester (Self-Heal)</div>
                    </div>
                    <div class="step-node completed">
                        <div class="step-circle">5</div>
                        <div class="step-label">Reviewer</div>
                    </div>
                    <div class="step-node completed">
                        <div class="step-circle">6</div>
                        <div class="step-label">Commit / PR</div>
                    </div>
                </div>

                <div class="progress-container" style="margin-top: 10px;">
                    <div class="progress-bar-bg" style="height: 12px;">
                        <div class="progress-bar-fill" style="width: 100%;"></div>
                    </div>
                    <div class="progress-labels">
                        <span>Status: <b>Pipeline Ready & Fully Verified</b></span>
                        <span>Multi-Agent Orchestration Active</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>🕒 Riwayat Eksekusi Task Otonom</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Run ID</th>
                            <th>Instruksi / Prompt</th>
                            <th>Branch</th>
                            <th>Status</th>
                            <th>Progress Bar</th>
                            <th>Waktu</th>
                        </tr>
                    </thead>
                    <tbody id="trajectory-runs-body">
                        <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Memuat riwayat trajektori...</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Section 4: Web Vibe Studio -->
        <section id="section-studio" class="content-section">
            <div class="studio-container">
                <div class="studio-chat">
                    <div class="studio-chat-header">
                        <span>💬 Percakapan & Task Studio</span>
                        <button class="btn btn-secondary" onclick="clearStudioChat()" style="padding: 3px 8px; font-size: 11px;">🗑️ Bersihkan Chat</button>
                    </div>
                    <div class="chat-box" id="studio-chat-box">
                        <div class="chat-bubble-wrapper assistant">
                            <div class="chat-bubble assistant">
                                <div class="bubble-action-btns">
                                    <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                                </div>
                                👋 <b>ACE Autonomous Software Engineer & Vibe Studio</b><br><br>
                                Anda bisa <b>memberikan perintah pengubahan kode</b> (misal: <i>"ganti judul Nexus menjadi BukuLokal"</i>, <i>"ubah warna navbar menjadi emerald"</i>) atau <b>berdiskusi santai</b>. ACE akan langsung memodifikasi file di codebase!
                            </div>
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="studio-prompt-input" placeholder="Ketik perintah coding atau pertanyaan Anda..." onkeydown="if(event.key==='Enter') sendStudioTask()">
                        <button class="btn btn-primary" id="btn-studio-send" onclick="sendStudioTask()">Kirim</button>
                    </div>
                </div>
                <div class="studio-preview">
                    <div class="preview-toolbar">
                        <div class="preview-tabs">
                            <button class="preview-tab-btn active" id="tab-code-btn" onclick="switchPreviewMode('code')">📄 Code Inspector</button>
                            <button class="preview-tab-btn" id="tab-visual-btn" onclick="switchPreviewMode('visual')">🌐 Live Visual Preview</button>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <select class="theme-select" id="inspector-file-select" onchange="loadFileToInspector(this.value)" style="padding: 4px 8px; font-size: 11.5px; height: 28px;">
                                <option value="public/index.html">public/index.html</option>
                                <option value="diff">Git Diff Terakhir</option>
                            </select>
                            <a id="preview-newtab-link" href="/preview" target="_blank" class="btn btn-secondary" style="padding: 3px 8px; font-size: 11px;">↗️ Buka di Tab Baru</a>
                        </div>
                    </div>
                    <div class="code-display" id="studio-code-display">// Memuat preview kode...</div>
                    <iframe class="iframe-preview" id="studio-iframe-preview" src="/preview" style="display: none;"></iframe>
                </div>
            </div>
        </section>

        <!-- Section 5: Terminal Hub -->
        <section id="section-terminal" class="content-section">
            <div class="card" style="max-width: 800px; margin-bottom: 24px;">
                <h2>💻 Terminal Vibe Coding Launcher</h2>
                <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">
                    Jalankan sesi coding interaktif langsung di terminal Mac Anda dengan perintah cepat di bawah:
                </p>

                <div style="background-color: var(--code-bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin: 16px 0; font-family: monospace; font-size: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <code style="color: var(--accent);">python3 src/ace/cli.py chat</code>
                    <button class="btn btn-secondary" onclick="copyText('python3 src/ace/cli.py chat')">📋 Salin Perintah</button>
                </div>

                <h3 style="margin-top: 18px; font-size: 14px;">Pintasan Cepat dalam Chat Terminal:</h3>
                <ul style="margin: 10px 0 0 20px; font-size: 13px; color: var(--text-muted); line-height: 1.8;">
                    <li><code>/files</code> — Melihat seluruh daftar file yang ada dalam proyek</li>
                    <li><code>/diff</code> — Melihat perubahan kode git diff terakhir</li>
                    <li><code>/clear</code> — Membersihkan riwayat percakapan sesi</li>
                    <li><code>/exit</code> — Mengakhiri sesi vibe coding</li>
                </ul>
            </div>
        </section>
    </main>

    <div class="toast" id="toast-msg">✅ Konfigurasi berhasil disimpan!</div>

    <script>
        let currentSection = 'setup';

        function switchSection(secId) {
            currentSection = secId;
            document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById('section-' + secId).classList.add('active');
            event.currentTarget.classList.add('active');

            const titleMap = {
                'setup': '⚙️ Setup & Konfigurasi ACE',
                'quotas': '📊 Monitoring Kuota & Penggunaan',
                'trajectory': '🔍 Observability & Visual Progress Bar',
                'studio': '💬 Web Vibe Studio',
                'terminal': '💻 Terminal Vibe Launcher'
            };
            document.getElementById('header-text').innerText = titleMap[secId] || 'ACE Control Center';

            if (secId === 'quotas') loadQuotas();
            if (secId === 'trajectory') loadTrajectory();
            if (secId === 'studio') {
                loadStudioChat();
                loadFilesDropdown();
                loadFileToInspector(document.getElementById('inspector-file-select').value);
            }
        }

        function switchPreviewMode(mode) {
            const codeEl = document.getElementById('studio-code-display');
            const iframeEl = document.getElementById('studio-iframe-preview');
            const codeBtn = document.getElementById('tab-code-btn');
            const visualBtn = document.getElementById('tab-visual-btn');

            if (mode === 'visual') {
                codeEl.style.display = 'none';
                iframeEl.style.display = 'block';
                iframeEl.src = '/preview?t=' + Date.now();
                codeBtn.classList.remove('active');
                visualBtn.classList.add('active');
            } else {
                codeEl.style.display = 'block';
                iframeEl.style.display = 'none';
                codeBtn.classList.add('active');
                visualBtn.classList.remove('active');
            }
        }

        function changeTheme(themeName) {
            document.body.className = themeName;
            localStorage.setItem('ace_theme', themeName);
        }

        function showToast(msg) {
            const t = document.getElementById('toast-msg');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 4000);
        }

        function copyText(text) {
            navigator.clipboard.writeText(text);
            showToast('📋 Teks disalin ke clipboard!');
        }

        function copyBubbleText(btn) {
            const bubble = btn.closest('.chat-bubble');
            const clone = bubble.cloneNode(true);
            const actionBtns = clone.querySelector('.bubble-action-btns');
            if (actionBtns) actionBtns.remove();
            
            const rawText = clone.innerText.trim();
            navigator.clipboard.writeText(rawText);
            showToast('📋 Teks disalin ke clipboard!');
        }

        function editBubblePrompt(btn) {
            const bubble = btn.closest('.chat-bubble');
            const clone = bubble.cloneNode(true);
            const actionBtns = clone.querySelector('.bubble-action-btns');
            if (actionBtns) actionBtns.remove();
            
            const rawPrompt = clone.innerText.trim();
            const input = document.getElementById('studio-prompt-input');
            input.value = rawPrompt;
            input.focus();
            input.setSelectionRange(input.value.length, input.value.length);
            showToast('✏️ Prompt dimuat ke kotak input untuk diedit!');
        }

        async function loadConfig() {
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                document.getElementById('input-key1').value = data.gemini_api_key_1 || '';
                document.getElementById('input-key2').value = data.gemini_api_key_2 || '';
                document.getElementById('input-ollama').value = data.ollama_base_url || 'http://localhost:11434';
                document.getElementById('input-github').value = data.github_token || '';
                document.getElementById('input-locale').value = data.locale || 'id';
            } catch (e) { console.error(e); }
        }

        async function saveConfiguration() {
            const payload = {
                gemini_api_key_1: document.getElementById('input-key1').value,
                gemini_api_key_2: document.getElementById('input-key2').value,
                ollama_base_url: document.getElementById('input-ollama').value,
                github_token: document.getElementById('input-github').value,
                locale: document.getElementById('input-locale').value
            };
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'ok') {
                    showToast('✅ Berhasil disimpan ke .env!');
                }
            } catch (e) {
                showToast('❌ Gagal menyimpan konfigurasi.');
            }
        }

        async function testKey(keyIndex) {
            const input = keyIndex === 1 ? document.getElementById('input-key1') : document.getElementById('input-key2');
            const keyVal = input.value.trim();
            if (!keyVal) {
                showToast('⚠️ Masukkan API Key terlebih dahulu.');
                return;
            }
            showToast('⏳ Menguji koneksi Gemini API...');
            try {
                const res = await fetch('/api/config/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'gemini', key: keyVal })
                });
                const data = await res.json();
                showToast(data.message);
            } catch (e) {
                showToast('❌ Gagal menghubungi endpoint.');
            }
        }

        async function testOllama() {
            const url = document.getElementById('input-ollama').value.trim();
            showToast('⏳ Menghubungi Ollama lokal...');
            try {
                const res = await fetch('/api/config/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'ollama', url: url })
                });
                const data = await res.json();
                showToast(data.message);
            } catch (e) {
                showToast('❌ Gagal menghubungi Ollama.');
            }
        }

        async function loadQuotas() {
            try {
                const res = await fetch('/api/quotas');
                const data = await res.json();
                const quotas = data.quotas || [];

                let totalFlashUsed = 0;
                let totalFlashLimit = 3000;
                let totalProUsed = 0;
                let totalProLimit = 100;
                let totalTokens = 0;

                const tbody = document.getElementById('quota-table-body');
                if (quotas.length === 0) {
                    tbody.innerHTML = `
                        <tr><td>gemini-flash</td><td>Key #1</td><td><span class="badge badge-success">Active</span></td><td>0</td><td>0</td><td>1,500</td></tr>
                        <tr><td>gemini-flash</td><td>Key #2</td><td><span class="badge badge-success">Active</span></td><td>0</td><td>0</td><td>1,500</td></tr>
                        <tr><td>gemini-pro</td><td>Key #1 & #2</td><td><span class="badge badge-warning">Active</span></td><td>0</td><td>0</td><td>100</td></tr>
                    `;
                } else {
                    tbody.innerHTML = quotas.map(q => {
                        const reqUsed = q.requests_used || 0;
                        const tokUsed = q.tokens_used || 0;
                        totalTokens += tokUsed;
                        if (q.provider === 'gemini-flash') totalFlashUsed += reqUsed;
                        if (q.provider === 'gemini-pro') totalProUsed += reqUsed;
                        return `
                            <tr>
                                <td><b>${q.provider}</b></td>
                                <td>Key #${q.api_key_id + 1}</td>
                                <td><span class="badge badge-success">Active</span></td>
                                <td><b>${reqUsed}</b></td>
                                <td>${tokUsed.toLocaleString()} tokens</td>
                                <td>${q.limit_requests.toLocaleString()}</td>
                            </tr>
                        `;
                    }).join('');
                }

                // Update Flash card
                document.getElementById('quota-flash-used').innerText = `Digunakan: ${totalFlashUsed} request`;
                const flashPct = Math.min(100, Math.round((totalFlashUsed / totalFlashLimit) * 100));
                document.getElementById('quota-flash-bar').style.width = `${Math.max(2, flashPct)}%`;

                // Update Pro card
                document.getElementById('quota-pro-used').innerText = `Digunakan: ${totalProUsed} request`;
                const proPct = Math.min(100, Math.round((totalProUsed / totalProLimit) * 100));
                document.getElementById('quota-pro-bar').style.width = `${proPct}%`;

                // Update tokens label
                if (totalTokens > 0) {
                    document.getElementById('tokens-total-label').innerText = `✅ ${totalTokens.toLocaleString()} tokens terbakar hari ini ($0.00)`;
                }
            } catch (e) {
                console.error(e);
            }
        }

        async function loadTrajectory() {
            try {
                const res = await fetch('/api/runs');
                const data = await res.json();
                const tbody = document.getElementById('trajectory-runs-body');
                if (!data.runs || data.runs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Belum ada task yang dieksekusi. Coba jalankan task di Web Studio!</td></tr>';
                    return;
                }
                tbody.innerHTML = data.runs.map(r => `
                    <tr>
                        <td><code>${r.id.substring(0,8)}</code></td>
                        <td><b>${r.user_prompt}</b></td>
                        <td><code>${r.branch_name || 'main'}</code></td>
                        <td><span class="badge ${r.status==='completed'?'badge-success':'badge-warning'}">${r.status}</span></td>
                        <td>
                            <div class="progress-bar-bg" style="height: 8px; width: 120px;">
                                <div class="progress-bar-fill" style="width: ${r.status==='completed'?'100%':'50%'};"></div>
                            </div>
                        </td>
                        <td>${new Date(r.started_at).toLocaleTimeString()}</td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }

        function formatMarkdown(text) {
            if (!text) return '';
            return text
                .replace(/\\n/g, '<br>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>')
                .replace(/`([^`]+)`/g, '<code>$1</code>');
        }

        function saveStudioChat() {
            const chatBox = document.getElementById('studio-chat-box');
            if (chatBox) {
                localStorage.setItem('ace_studio_chat_history', chatBox.innerHTML);
            }
        }

        function loadStudioChat() {
            const saved = localStorage.getItem('ace_studio_chat_history');
            const chatBox = document.getElementById('studio-chat-box');
            if (saved && chatBox) {
                chatBox.innerHTML = saved;
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        function clearStudioChat() {
            const chatBox = document.getElementById('studio-chat-box');
            if (chatBox) {
                chatBox.innerHTML = `
                    <div class="chat-bubble-wrapper assistant">
                        <div class="chat-bubble assistant">
                            <div class="bubble-action-btns">
                                <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                            </div>
                            👋 <b>ACE Autonomous Software Engineer & Vibe Studio</b><br><br>
                            Percakapan telah dibersihkan. Anda bisa mulai mengetik ide coding atau instruksi pengubahan file baru!
                        </div>
                    </div>
                `;
                localStorage.removeItem('ace_studio_chat_history');
                showToast('🧹 Riwayat chat dibersihkan!');
            }
        }

        async function loadFilesDropdown() {
            try {
                const res = await fetch('/api/files');
                const data = await res.json();
                const select = document.getElementById('inspector-file-select');
                if (data.files && data.files.length > 0) {
                    select.innerHTML = '<option value="diff">🔍 Git Diff Terakhir</option>' + 
                        data.files.map(f => `<option value="${f}">${f}</option>`).join('');
                    if (data.files.includes('public/index.html')) {
                        select.value = 'public/index.html';
                    }
                }
            } catch (e) {}
        }

        async function loadFileToInspector(filePath) {
            const codeDisplay = document.getElementById('studio-code-display');
            if (filePath === 'diff') {
                try {
                    const res = await fetch('/api/diff');
                    const data = await res.json();
                    codeDisplay.innerText = data.diff || '// Tidak ada perubahan git yang belum dicommit.';
                } catch (e) { codeDisplay.innerText = '// Gagal memuat diff.'; }
                return;
            }

            try {
                const res = await fetch(`/api/file?path=${encodeURIComponent(filePath)}`);
                const data = await res.json();
                if (data.content) {
                    codeDisplay.innerText = data.content;
                } else if (data.error) {
                    codeDisplay.innerText = `// Error: ${data.error}`;
                }
            } catch (e) {
                codeDisplay.innerText = `// Gagal memuat file: ${filePath}`;
            }
        }

        async function sendStudioTask() {
            const input = document.getElementById('studio-prompt-input');
            const prompt = input.value.trim();
            if (!prompt) return;

            const chatBox = document.getElementById('studio-chat-box');
            
            // Append User Chat Bubble with Copy and Edit buttons
            chatBox.innerHTML += `
                <div class="chat-bubble-wrapper user">
                    <div class="chat-bubble user">
                        <div class="bubble-action-btns">
                            <button class="bubble-btn" onclick="editBubblePrompt(this)">✏️ Edit</button>
                            <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                        </div>
                        ${prompt}
                    </div>
                </div>
            `;
            input.value = '';
            saveStudioChat();

            const btn = document.getElementById('btn-studio-send');
            btn.disabled = true;
            btn.innerText = 'Thinking...';

            const thinkingWrapper = document.createElement('div');
            thinkingWrapper.className = 'chat-bubble-wrapper assistant';
            const thinking = document.createElement('div');
            thinking.className = 'chat-bubble assistant';
            thinking.innerHTML = '🤖 <i>ACE sedang merancang arsitektur, menulis/memodifikasi kode & menjalankan validasi...</i>';
            thinkingWrapper.appendChild(thinking);
            chatBox.appendChild(thinkingWrapper);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                const data = await res.json();
                
                if (data.error) {
                    thinking.innerHTML = `
                        <div class="bubble-action-btns">
                            <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                        </div>
                        <span style="color: var(--rose);">❌ <b>Error:</b> ${data.error}</span>
                    `;
                } else if (data.type === 'chat') {
                    // Conversational AI Response
                    thinking.innerHTML = `
                        <div class="bubble-action-btns">
                            <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                        </div>
                        <b>🤖 ACE Assistant:</b><br><br>${formatMarkdown(data.reply)}
                    `;
                } else {
                    // Coding Task Completion with Full Explanation
                    const filesCount = data.files_modified ? data.files_modified.length : 0;
                    const isSuccess = (data.status === 'completed');

                    thinking.innerHTML = `
                        <div class="bubble-action-btns">
                            <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                        </div>
                        <div style="font-size: 14px; font-weight: 700; margin-bottom: 8px;">
                            ${isSuccess ? '✅ Task Selesai!' : '⚠️ Task Selesai dengan Catatan'}
                        </div>
                        <div style="font-size: 13px; color: var(--text-main); margin-bottom: 10px;">
                            ${formatMarkdown(data.explanation || 'Pekerjaan selesai diproses.')}
                        </div>
                        <div style="font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border); padding-top: 8px;">
                            • <b>Branch:</b> <code>${data.branch}</code> &bull; <b>Files:</b> ${filesCount} file
                        </div>
                    `;

                    // Refresh inspector dropdown & reload file
                    await loadFilesDropdown();
                    if (data.files_modified && data.files_modified.length > 0) {
                        const firstFile = data.files_modified[0];
                        const targetPath = firstFile.path || 'public/index.html';
                        document.getElementById('inspector-file-select').value = targetPath;
                        await loadFileToInspector(targetPath);
                    }

                    // Auto refresh iframe visual preview
                    const iframeEl = document.getElementById('studio-iframe-preview');
                    if (iframeEl) iframeEl.src = '/preview?t=' + Date.now();
                }
            } catch (e) {
                thinking.innerHTML = `
                    <div class="bubble-action-btns">
                        <button class="bubble-btn" onclick="copyBubbleText(this)">📋 Salin</button>
                    </div>
                    <span style="color: var(--rose);">❌ Error: ${e.message}</span>
                `;
            } finally {
                btn.disabled = false;
                btn.innerText = 'Kirim';
                chatBox.scrollTop = chatBox.scrollHeight;
                saveStudioChat();
            }
        }

        // Init
        const savedTheme = localStorage.getItem('ace_theme') || 'theme-linear';
        document.body.className = savedTheme;
        document.getElementById('theme-selector').value = savedTheme;
        loadConfig();
        loadStudioChat();
        loadFilesDropdown();
    </script>
</body>
</html>
"""


def _is_conversational_prompt(prompt: str) -> bool:
    """Classify if user input is an inquiry/chat or an action-oriented coding command."""
    p = prompt.strip().lower()
    
    # Explicit coding & modifying action keywords
    code_actions = (
        "ganti", "ubah", "edit", "update", "replace", "sesuaikan", "hapus", "perbaiki",
        "refactor", "switch", "rename", "buatkan", "tambahkan", "bikin", "tuliskan",
        "code", "modifikasi", "tulis", "create", "build", "scaffold", "add", "fix",
        "set", "jadikan", "masukkan"
    )
    if any(kw in p for kw in code_actions):
        return False

    # Conversational question markers
    chat_starters = (
        "kenapa", "mengapa", "apa", "bagaimana", "siapa", "dimana", "kapan", "apakah",
        "why", "what", "how", "who", "where", "when", "is ", "are ", "can ", "could ",
        "jelaskan", "tolong jelaskan", "explain", "tell me", "help me understand"
    )
    if p.endswith("?") or any(p.startswith(w) for w in chat_starters):
        return True

    # Short queries that are clearly questions or feedback
    if len(p.split()) <= 5 and any(w in p for w in ("kenapa", "gagal", "error", "rusak", "mengapa", "status", "bisa", "halo", "hai", "pagi", "sore")):
        return True

    return False


class ControlCenterHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request handler for ACE Web Control Center."""

    supervisor = SupervisorAgent()
    router = LLMRouter()

    def do_GET(self):
        load_dotenv()
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/ui", "/dashboard", "/hub"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(CONTROL_CENTER_HTML.encode("utf-8"))
            return

        if parsed.path == "/preview":
            # Dynamic preview: start or redirect to live dev server runtime
            try:
                from ace.preview.runtime import PreviewRuntime
                cwd = str(Path.cwd())
                runtime = PreviewRuntime.get_or_create(cwd)
                if not runtime.is_alive():
                    preview_url = runtime.start(cwd, port=8888)
                else:
                    preview_url = runtime.url
                # Redirect to the live dev server
                self.send_response(302)
                self.send_header("Location", preview_url or "http://localhost:8888")
                self.end_headers()
            except Exception:
                # Fallback: serve public/index.html if preview runtime fails
                target_path = Path("public/index.html")
                if target_path.exists():
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(target_path.read_bytes())
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"<html><body style='font-family:sans-serif;padding:40px;text-align:center;background:#0f172a;color:#94a3b8;'><h2>Preview runtime not available</h2><p>Run your project server manually or trigger a task first.</p></body></html>")
            return

        if parsed.path == "/api/preview/status":
            # Return JSON status of the preview runtime
            try:
                from ace.preview.runtime import PreviewRuntime
                cwd = str(Path.cwd())
                runtime = PreviewRuntime.get_or_create(cwd)
                status = {
                    "started": runtime.is_alive(),
                    "url": runtime.url,
                    "verified": runtime.verified,
                }
            except Exception as e:
                status = {"started": False, "url": None, "verified": False, "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode("utf-8"))
            return

        if parsed.path.startswith("/public/"):
            rel_path = parsed.path.replace("/public/", "").strip("/")
            target_path = Path("public") / rel_path
            if target_path.exists() and target_path.is_file():
                content_type = "text/html; charset=utf-8"
                if target_path.suffix == ".css":
                    content_type = "text/css"
                elif target_path.suffix == ".js":
                    content_type = "application/javascript"
                elif target_path.suffix == ".json":
                    content_type = "application/json"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(target_path.read_bytes())
            else:
                self.send_response(404)
                self.end_headers()
            return

        if parsed.path == "/api/files":
            files = []
            for p in Path.cwd().glob("public/**/*"):
                if p.is_file():
                    files.append(str(p.relative_to(Path.cwd())))
            for p in Path.cwd().glob("src/**/*.py"):
                if p.is_file():
                    files.append(str(p.relative_to(Path.cwd())))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"files": files[:40]}).encode("utf-8"))
            return

        if parsed.path == "/api/file":
            qs = parse_qs(parsed.query)
            file_path_str = qs.get("path", [""])[0].strip()
            target = (Path.cwd() / file_path_str).resolve()
            if str(target).startswith(str(Path.cwd())) and target.exists() and target.is_file():
                content = target.read_text(encoding="utf-8", errors="replace")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"path": file_path_str, "content": content}).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "File tidak ditemukan"}).encode("utf-8"))
            return

        if parsed.path == "/api/config":
            cfg = ConfigManager.get_config()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(cfg).encode("utf-8"))
            return

        if parsed.path == "/api/quotas":
            init_db()
            tracker = QuotaTracker()
            quotas = tracker.get_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"quotas": quotas}).encode("utf-8"))
            return

        if parsed.path == "/api/runs":
            init_db()
            runs = []
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, user_prompt, status, branch_name, total_tokens, started_at FROM agent_runs ORDER BY started_at DESC LIMIT 20")
                    runs = [dict(row) for row in cursor.fetchall()]
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"runs": runs}).encode("utf-8"))
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
        load_dotenv()
        parsed = urlparse(self.path)

        if parsed.path == "/api/config":
            content_length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            success = ConfigManager.save_config(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok" if success else "error"}).encode("utf-8"))
            return

        if parsed.path == "/api/config/test":
            content_length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            test_type = payload.get("type", "")
            if test_type == "gemini":
                success, msg = ConfigManager.test_gemini_key(payload.get("key", ""))
            elif test_type == "ollama":
                success, msg = ConfigManager.test_ollama_url(payload.get("url", ""))
            else:
                success, msg = False, "Unknown test type"

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "message": msg}).encode("utf-8"))
            return

        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            prompt = payload.get("prompt", "").strip()

            try:
                # 1. Smart Intent Routing: Check if prompt is purely Conversational Inquiry
                if _is_conversational_prompt(prompt):
                    route = self.router.route(complexity=TaskComplexity.LOW)
                    system_instruction = (
                        "You are ACE (Autonomous Code Engineer), an expert pair-programming AI assistant. "
                        "The user is asking a question or seeking clarification in chat. "
                        "Answer clearly, accurately, and politely in Indonesian (or English if prompted). "
                        "Do not output raw file generation code blocks unless specifically requested. "
                        "Be helpful and concise."
                    )
                    chat_res = asyncio.run(route.generate(
                        prompt=prompt,
                        system_instruction=system_instruction
                    ))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "type": "chat",
                        "reply": chat_res.get("text", ""),
                        "tokens_used": chat_res.get("tokens_used", 0)
                    }).encode("utf-8"))
                    return

                # 2. Otherwise: Execute Autonomous Coding Task & Code Restructuring Pipeline
                result = asyncio.run(self.supervisor.run_task(prompt=prompt, locale="id"))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"type": "task", **result}).encode("utf-8"))
            except Exception as e:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def launch_control_center(port: int = 8000) -> None:
    """Launch the ACE Web Control Center on the specified port."""
    server = HTTPServer(("0.0.0.0", port), ControlCenterHTTPHandler)
    print("=" * 65)
    print(f"🚀 ACE CONTROL CENTER ACTIVE AT: http://localhost:{port}")
    print("=" * 65)
    print("👉 Buka link di atas pada browser untuk Setup, Monitoring & Vibe Coding!\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Control Center dihentikan.")
