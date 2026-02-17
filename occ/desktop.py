"""OCC desktop app (Windows-friendly Tkinter frontend).

Design goals inspired by Fluent-style principles:
- clear hierarchy and focus
- low-clutter workbench with explicit command preview
- persistent settings and run history
- fast access to core OCC workflows
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import queue
import re
import shlex
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    from .version import get_version
except ImportError:
    # Support direct script execution (e.g., PyInstaller entry as desktop.py).
    from occ.version import get_version

try:
    from .ai_assistant import AssistantError, ask_openai
except ImportError:
    from occ.ai_assistant import AssistantError, ask_openai

try:
    from .offline_assistant import ask_offline
except ImportError:
    from occ.offline_assistant import ask_offline


def _detect_language() -> str:
    candidates = [
        os.getenv("OCC_LANG"),
        os.getenv("LC_ALL"),
        os.getenv("LC_MESSAGES"),
        os.getenv("LANG"),
    ]
    for raw in candidates:
        norm = str(raw or "").strip().lower()
        if not norm:
            continue
        if norm == "c" or norm.startswith("c.") or norm == "posix":
            continue
        if norm.startswith("es"):
            return "es"
        return "en"
    return "en"


APP_LANGUAGE = _detect_language()


def _tr(en: str, es: str) -> str:
    return es if APP_LANGUAGE == "es" else en


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now_utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _fmt_cmd(cmd: Sequence[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(list(cmd))
    return " ".join(shlex.quote(x) for x in cmd)


RELEASE_STABLE_URL = "https://github.com/MarcoAIsaac/OCC/releases/latest"
RELEASE_DESKTOP_ROLLING_URL = "https://github.com/MarcoAIsaac/OCC/releases/tag/desktop-latest"
RELEASE_DESKTOP_ROLLING_BASE = (
    "https://github.com/MarcoAIsaac/OCC/releases/download/desktop-latest/"
)


class OCCDesktopApp(tk.Tk):
    BG = "#0b1220"
    SURFACE = "#111827"
    PANEL = "#0f172a"
    BORDER = "#1f2937"
    TEXT = "#e5e7eb"
    MUTED = "#94a3b8"
    ACCENT = "#0ea5e9"
    ACCENT_ACTIVE = "#0284c7"
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    BUTTON_PRIMARY_BG = "#0ea5e9"
    BUTTON_PRIMARY_HOVER = "#0284c7"
    BUTTON_SECONDARY_BG = "#13213a"
    BUTTON_SECONDARY_HOVER = "#1b2c4b"
    BUTTON_DANGER_BG = "#ef4444"
    BUTTON_DANGER_HOVER = "#dc2626"

    VERDICT_RE = re.compile(r"\b(PASS|FAIL|NO-EVAL)(?:\([^)]+\))?\b")

    def __init__(self) -> None:
        super().__init__()

        self.title("OCC Desktop")
        self.geometry("1280x840")
        self.minsize(1080, 700)

        self.repo_root = Path(__file__).resolve().parents[1]
        self.app_dir = Path.home() / ".occ_desktop"
        self.settings_file = self.app_dir / "settings.json"
        self.db_file = self.app_dir / "occ_desktop.db"

        self.workspace_var = tk.StringVar(value=str(self.repo_root))
        self.claim_var = tk.StringVar(
            value=str(self.repo_root / "examples" / "claim_specs" / "minimal_pass.yaml")
        )
        self.profile_var = tk.StringVar(value="core")
        self.suite_var = tk.StringVar(value="extensions")
        self.module_name_var = tk.StringVar(value="")
        self.create_prediction_var = tk.BooleanVar(value=True)
        self.verify_generated_var = tk.BooleanVar(value=False)
        self.ai_provider_var = tk.StringVar(value="offline")
        self.ai_model_var = tk.StringVar(value="gpt-4.1-mini")
        self.ai_timeout_var = tk.StringVar(value="45")
        self.ai_include_context_var = tk.BooleanVar(value=True)
        self.ai_system_prompt_var = tk.StringVar(
            value=(
                "You are the OCC Desktop assistant. Focus on actionable guidance for "
                "judges, locks, module flow, and reproducible execution."
            )
        )
        self.lab_claims_dir_var = tk.StringVar(
            value=str(self.repo_root / "examples" / "claim_specs")
        )
        self.lab_out_dir_var = tk.StringVar(
            value=str(self.repo_root / ".occ_lab" / "latest")
        )
        self.lab_recursive_var = tk.BooleanVar(value=False)
        self.lab_profile_core_var = tk.BooleanVar(value=True)
        self.lab_profile_nuclear_var = tk.BooleanVar(value=True)
        self.lab_strict_trace_var = tk.BooleanVar(value=False)
        self.lab_fail_on_non_pass_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value=_tr("Ready", "Listo"))
        self.command_preview_var = tk.StringVar(value="-")
        self.verdict_var = tk.StringVar(value="-")
        self.last_run_var = tk.StringVar(value="-")
        self.metrics_var = tk.StringVar(
            value=_tr(
                "Runs: 0 | PASS: 0 | FAIL: 0 | NO-EVAL: 0",
                "Ejecuciones: 0 | PASS: 0 | FAIL: 0 | NO-EVAL: 0",
            )
        )
        self.assistant_status_var = tk.StringVar(
            value=_tr("Assistant idle", "Asistente inactivo")
        )
        self.lab_status_var = tk.StringVar(value=_tr("Lab idle", "Lab inactivo"))
        self.version_var = tk.StringVar(value=f"v{get_version()}")
        self.clock_var = tk.StringVar(value=_now_text())
        self.lab_runs_var = tk.StringVar(value="0")
        self.lab_pass_var = tk.StringVar(value="0")
        self.lab_fail_var = tk.StringVar(value="0")
        self.lab_no_eval_var = tk.StringVar(value="0")
        self.lab_divergence_var = tk.StringVar(value="0")

        self._queue: "queue.Queue[Tuple[str, Dict[str, Any]]]" = queue.Queue()
        self._proc: Optional[subprocess.Popen[str]] = None
        self._db_conn: Optional[sqlite3.Connection] = None
        self._running = False
        self._running_label = ""
        self._running_started_at = 0.0
        self._running_started_text = "-"
        self._current_verdict = ""
        self._last_cmd: List[str] = []
        self._run_log_buffer: List[str] = []
        self._stats_total_runs = 0
        self._stats_pass = 0
        self._stats_fail = 0
        self._stats_no_eval = 0
        self._assistant_running = False
        self._assistant_last_reply = ""
        self._assistant_output_text: Optional[tk.Text] = None
        self._assistant_prompt_text: Optional[tk.Text] = None
        self._assistant_system_text: Optional[tk.Text] = None
        self._assistant_api_key_var = tk.StringVar(value="")
        self._assistant_send_button: Optional[tk.Button] = None
        self._assistant_copy_button: Optional[tk.Button] = None
        self._assistant_clear_button: Optional[tk.Button] = None
        self._lab_output_text: Optional[tk.Text] = None

        self._buttons: List[Any] = []
        self._history_commands: Dict[str, List[str]] = {}
        self._history_db_ids: Dict[str, int] = {}

        self._init_persistence()
        self._load_settings()
        env_api_key = str(os.getenv("OPENAI_API_KEY") or "").strip()
        if env_api_key:
            self._assistant_api_key_var.set(env_api_key)
        self._configure_style()
        self._apply_window_branding()
        self._build_menu()
        self._build_ui()
        self._load_persisted_history()
        self._refresh_stats_from_tree()
        self._bind_shortcuts()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._drain_queue)
        self.after(1000, self._tick_clock)

    def _configure_style(self) -> None:
        self.configure(bg=self.BG)
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("App.TFrame", background=self.BG)
        style.configure("Surface.TFrame", background=self.SURFACE)
        style.configure("Panel.TFrame", background=self.PANEL)

        style.configure(
            "Header.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI Semibold", 17),
        )
        style.configure(
            "SubHeader.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "Body.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=self.PANEL,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "SidebarTitle.TLabel",
            background=self.SURFACE,
            foreground=self.TEXT,
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "HeroTitle.TLabel",
            background=self.PANEL,
            foreground="#f8fafc",
            font=("Segoe UI Semibold", 14),
        )
        style.configure(
            "HeroBody.TLabel",
            background=self.PANEL,
            foreground="#cbd5e1",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Metric.TLabel",
            background=self.PANEL,
            foreground="#7dd3fc",
            font=("Segoe UI Semibold", 10),
        )

        style.configure(
            "TNotebook",
            background=self.BG,
            borderwidth=0,
            tabmargins=[0, 0, 0, 0],
        )
        style.configure(
            "TNotebook.Tab",
            background=self.SURFACE,
            foreground=self.TEXT,
            padding=(12, 8),
            font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.PANEL), ("active", self.SURFACE)],
            foreground=[("selected", self.TEXT), ("active", self.TEXT)],
        )

        style.configure(
            "Primary.TButton",
            background=self.ACCENT,
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            padding=(12, 8),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Primary.TButton",
            background=[("pressed", self.ACCENT_ACTIVE), ("active", self.ACCENT_ACTIVE)],
            foreground=[("disabled", "#9ca3af")],
        )

        style.configure(
            "Ghost.TButton",
            background=self.PANEL,
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            borderwidth=1,
            padding=(10, 8),
            font=("Segoe UI", 10),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", self.SURFACE)],
            foreground=[("disabled", "#6b7280")],
        )

        style.configure(
            "Danger.TButton",
            background=self.DANGER,
            foreground="#ffffff",
            borderwidth=0,
            padding=(10, 8),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "Danger.TButton",
            background=[("pressed", "#dc2626"), ("active", "#dc2626")],
            foreground=[("disabled", "#9ca3af")],
        )

        style.configure(
            "Sidebar.TButton",
            background=self.SURFACE,
            foreground=self.TEXT,
            borderwidth=0,
            anchor="w",
            padding=(12, 10),
            font=("Segoe UI", 10),
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", self.PANEL)],
            foreground=[("disabled", "#6b7280")],
        )

        style.configure(
            "Input.TEntry",
            fieldbackground="#0f1a2b",
            foreground=self.TEXT,
            insertcolor=self.TEXT,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER,
            padding=6,
        )
        style.configure(
            "Input.TCombobox",
            fieldbackground="#0f1a2b",
            foreground=self.TEXT,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER,
            darkcolor=self.BORDER,
            arrowsize=14,
            padding=5,
        )

        style.configure(
            "Status.Horizontal.TProgressbar",
            troughcolor=self.BORDER,
            background=self.ACCENT,
            borderwidth=0,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
        )
        style.configure(
            "Card.TLabelframe",
            background=self.PANEL,
            bordercolor=self.BORDER,
            borderwidth=1,
            relief=tk.SOLID,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "TCheckbutton",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", self.PANEL)],
            foreground=[("disabled", "#6b7280")],
        )
        style.configure(
            "Treeview",
            background="#0b1324",
            foreground=self.TEXT,
            fieldbackground="#0b1324",
            bordercolor=self.BORDER,
            rowheight=26,
        )
        style.configure(
            "Treeview.Heading",
            background=self.SURFACE,
            foreground=self.TEXT,
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 9),
        )
        style.map(
            "Treeview",
            background=[("selected", "#1d4ed8")],
            foreground=[("selected", "#ffffff")],
        )

    def _build_menu(self) -> None:
        menu = tk.Menu(
            self,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
        )

        file_menu = tk.Menu(
            menu,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
        )
        file_menu.add_command(
            label=_tr("Open workspace", "Abrir workspace"),
            command=self._pick_workspace,
        )
        file_menu.add_command(label=_tr("Open claim", "Abrir claim"), command=self._pick_claim)
        file_menu.add_separator()
        file_menu.add_command(label=_tr("Save output", "Guardar salida"), command=self._save_output)
        file_menu.add_command(label=_tr("Exit", "Salir"), command=self._on_close)
        menu.add_cascade(label=_tr("File", "Archivo"), menu=file_menu)

        run_menu = tk.Menu(
            menu,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
        )
        run_menu.add_command(
            label=_tr("Judge claim", "Evaluar claim"),
            command=lambda: self._run_action("judge"),
        )
        run_menu.add_command(
            label=_tr("Verify suite", "Verificar suite"),
            command=lambda: self._run_action("verify"),
        )
        run_menu.add_command(
            label=_tr("Module flow", "Flujo de modulo"),
            command=lambda: self._run_action("module_flow"),
        )
        run_menu.add_command(
            label=_tr("Run experiment lab", "Ejecutar experiment lab"),
            command=lambda: self._run_action("lab_run"),
        )
        run_menu.add_separator()
        run_menu.add_command(
            label=_tr("Stop running command", "Detener comando"),
            command=self._stop_running,
        )
        menu.add_cascade(label=_tr("Run", "Ejecutar"), menu=run_menu)

        tools_menu = tk.Menu(
            menu,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
        )
        tools_menu.add_command(
            label=_tr("Release doctor", "Release doctor"),
            command=lambda: self._run_action("release_doctor"),
        )
        tools_menu.add_command(
            label=_tr("Docs i18n audit", "Auditar docs i18n"),
            command=lambda: self._run_action("docs_i18n"),
        )
        tools_menu.add_command(
            label=_tr("CI doctor", "CI doctor"),
            command=lambda: self._run_action("ci_doctor"),
        )
        tools_menu.add_command(
            label=_tr("Generate release notes", "Generar release notes"),
            command=lambda: self._run_action("release_notes"),
        )
        menu.add_cascade(label=_tr("Tools", "Herramientas"), menu=tools_menu)

        ai_menu = tk.Menu(
            menu,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
        )
        ai_menu.add_command(
            label=_tr("OpenAI API docs", "Docs API OpenAI"),
            command=lambda: webbrowser.open("https://platform.openai.com/docs"),
        )
        ai_menu.add_command(
            label=_tr("Set OPENAI_API_KEY", "Definir OPENAI_API_KEY"),
            command=self._show_set_api_key_dialog,
        )
        menu.add_cascade(label=_tr("Assistant", "Asistente"), menu=ai_menu)

        help_menu = tk.Menu(
            menu,
            tearoff=False,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
        )
        help_menu.add_command(
            label=_tr("Documentation portal", "Portal de documentacion"),
            command=lambda: webbrowser.open("https://marcoaisaac.github.io/OCC/"),
        )
        help_menu.add_command(
            label=_tr("Latest release", "Ultimo release"),
            command=lambda: webbrowser.open(RELEASE_STABLE_URL),
        )
        help_menu.add_separator()
        help_menu.add_command(label=_tr("About", "Acerca de"), command=self._show_about_dialog)
        menu.add_cascade(label=_tr("Help", "Ayuda"), menu=help_menu)

        self.configure(menu=menu)

    def _tick_clock(self) -> None:
        self.clock_var.set(_now_text())
        self.after(1000, self._tick_clock)

    def _show_about_dialog(self) -> None:
        messagebox.showinfo(
            "OCC Desktop",
            _tr(
                f"OCC Desktop\nVersion: {self.version_var.get()}\n\n"
                "Windows workstation for OCC runtime operations.",
                f"OCC Desktop\nVersion: {self.version_var.get()}\n\n"
                "Estacion de trabajo Windows para operaciones del runtime OCC.",
            ),
        )

    def _apply_window_branding(self) -> None:
        try:
            icon = tk.PhotoImage(width=64, height=64)
            icon.put("#0b1220", to=(0, 0, 64, 64))
            icon.put("#1e293b", to=(6, 6, 58, 58))
            icon.put("#0ea5e9", to=(10, 10, 54, 22))
            icon.put("#22d3ee", to=(10, 22, 54, 34))
            icon.put("#38bdf8", to=(10, 34, 54, 54))
            icon.put("#f8fafc", to=(18, 18, 46, 46))
            icon.put("#0f172a", to=(22, 22, 42, 42))
            self._brand_icon = icon  # keep reference
            self.iconphoto(True, self._brand_icon)
        except Exception:
            pass

    def _init_persistence(self) -> None:
        self.app_dir.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(self.db_file)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    action TEXT NOT NULL,
                    command_text TEXT NOT NULL,
                    exit_code INTEGER NOT NULL,
                    duration_s REAL NOT NULL,
                    verdict TEXT NOT NULL,
                    output_excerpt TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_run_history_started_at
                ON run_history(started_at DESC)
                """
            )
            conn.commit()
            self._db_conn = conn
        except Exception as e:
            self._db_conn = None
            self.status_var.set(_tr(f"DB offline: {e}", f"BD inactiva: {e}"))

    def _load_persisted_history(self, limit: int = 250) -> None:
        if self._db_conn is None:
            return
        try:
            rows = self._db_conn.execute(
                """
                SELECT id, started_at, action, exit_code, duration_s, verdict, command_text
                FROM run_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        except Exception:
            return

        for row in reversed(rows):
            row_id, started_at, action, rc, duration_s, verdict, command_text = row
            command_value = str(command_text or "")
            try:
                parsed_command = json.loads(command_value)
                if isinstance(parsed_command, list):
                    command = [str(x) for x in parsed_command]
                else:
                    command = [command_value]
            except json.JSONDecodeError:
                command = [command_value]
            self._insert_history_row(
                started_at=str(started_at),
                action=str(action),
                rc=int(rc),
                duration_s=float(duration_s),
                verdict=str(verdict or "-"),
                command=command,
                db_id=int(row_id),
            )

    def _persist_history_row(
        self,
        started_at: str,
        action: str,
        rc: int,
        duration_s: float,
        verdict: str,
        command: Sequence[str],
        output_excerpt: str,
    ) -> Optional[int]:
        if self._db_conn is None:
            return None
        cmd_text = json.dumps(list(command), ensure_ascii=True)
        try:
            cursor = self._db_conn.execute(
                """
                INSERT INTO run_history (
                    started_at,
                    action,
                    command_text,
                    exit_code,
                    duration_s,
                    verdict,
                    output_excerpt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    started_at,
                    action,
                    cmd_text,
                    rc,
                    duration_s,
                    verdict or "-",
                    output_excerpt,
                ),
            )
            self._db_conn.commit()
            last_id = cursor.lastrowid
            return int(last_id) if last_id is not None else None
        except Exception:
            return None

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, style="App.TFrame", padding=(14, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=_tr("OCC Desktop Workbench", "OCC Workbench Escritorio"),
            style="Header.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=_tr(
                "Operational runtime dashboard for judge, verify, module flow and release ops",
                "Panel operacional para judge, verify, flujo de modulo y operaciones release",
            ),
            style="SubHeader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        right = ttk.Frame(header, style="App.TFrame")
        right.grid(row=0, column=1, rowspan=2, sticky="e")

        version_chip = tk.Label(
            right,
            textvariable=self.version_var,
            bg="#0f172a",
            fg="#7dd3fc",
            font=("Segoe UI Semibold", 11),
            padx=10,
            pady=4,
        )
        version_chip.pack(anchor="e")

        clock_chip = tk.Label(
            right,
            textvariable=self.clock_var,
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        )
        clock_chip.pack(anchor="e", pady=(4, 0))

        main = ttk.Frame(self, style="App.TFrame", padding=(12, 0, 12, 12))
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)

        self._build_sidebar(main)
        self._build_content(main)

        status = ttk.Frame(self, style="Panel.TFrame", padding=(10, 8))
        status.grid(row=2, column=0, sticky="ew")
        status.grid_columnconfigure(0, weight=1)
        ttk.Label(status, textvariable=self.status_var, style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        sidebar = ttk.Frame(parent, style="Surface.TFrame", padding=10)
        sidebar.grid(row=0, column=0, sticky="nsw")

        ttk.Label(sidebar, text=_tr("Actions", "Acciones"), style="SidebarTitle.TLabel").pack(
            fill=tk.X,
            pady=(4, 8),
        )

        self._add_sidebar_button(sidebar, _tr("Judge claim", "Evaluar claim"), "judge")
        self._add_sidebar_button(sidebar, _tr("Verify suite", "Verificar suite"), "verify")
        self._add_sidebar_button(sidebar, _tr("Module flow", "Flujo de modulo"), "module_flow")
        self._add_sidebar_button(sidebar, _tr("Experiment lab", "Experiment lab"), "lab_run")

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(
            sidebar,
            text=_tr("Maintenance", "Mantenimiento"),
            style="SidebarTitle.TLabel",
        ).pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self._add_sidebar_button(
            sidebar,
            _tr("Release doctor", "Release doctor"),
            "release_doctor",
            primary=False,
        )
        self._add_sidebar_button(
            sidebar,
            _tr("Docs i18n audit", "Auditar docs i18n"),
            "docs_i18n",
            primary=False,
        )
        self._add_sidebar_button(sidebar, _tr("CI doctor", "CI doctor"), "ci_doctor", primary=False)
        self._add_sidebar_button(
            sidebar,
            _tr("Generate release notes", "Generar release notes"),
            "release_notes",
            primary=False,
        )

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        stop_btn = self._create_modern_button(
            sidebar,
            label=_tr("Stop running command", "Detener comando"),
            command=self._stop_running,
            variant="danger",
        )
        stop_btn.pack(fill=tk.X, pady=(2, 6))
        self._buttons.append(stop_btn)

        link_row = ttk.Frame(sidebar, style="Surface.TFrame")
        link_row.pack(fill=tk.X, pady=(6, 0))
        release_btn = self._create_modern_button(
            link_row,
            label=_tr("Open desktop-latest release", "Abrir release desktop-latest"),
            command=lambda: self._open_url(RELEASE_DESKTOP_ROLLING_URL),
            variant="ghost",
        )
        release_btn.pack(fill=tk.X)

    def _add_sidebar_button(
        self,
        parent: ttk.Frame,
        label: str,
        action: str,
        primary: bool = True,
    ) -> None:
        btn = self._create_modern_button(
            parent,
            label=label,
            command=self._make_action_handler(action),
            variant="primary" if primary else "ghost",
        )
        btn.pack(fill=tk.X, pady=4)
        self._buttons.append(btn)

    def _create_modern_button(
        self,
        parent: tk.Widget,
        label: str,
        command: Callable[[], None],
        variant: str = "primary",
    ) -> tk.Button:
        palette = {
            "primary": {
                "bg": self.BUTTON_PRIMARY_BG,
                "hover": self.BUTTON_PRIMARY_HOVER,
                "press": "#0369a1",
                "fg": "#ffffff",
            },
            "ghost": {
                "bg": self.BUTTON_SECONDARY_BG,
                "hover": self.BUTTON_SECONDARY_HOVER,
                "press": "#14203a",
                "fg": "#e2e8f0",
            },
            "danger": {
                "bg": self.BUTTON_DANGER_BG,
                "hover": self.BUTTON_DANGER_HOVER,
                "press": "#b91c1c",
                "fg": "#ffffff",
            },
        }
        colors = palette.get(variant, palette["ghost"])
        btn = tk.Button(
            parent,
            text=label,
            command=command,
            bg=colors["bg"],
            fg=colors["fg"],
            activebackground=colors["hover"],
            activeforeground=colors["fg"],
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=9,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
            disabledforeground="#9ca3af",
        )

        def on_enter(_event: tk.Event[Any]) -> None:
            if str(btn.cget("state")) != tk.DISABLED:
                btn.configure(bg=colors["hover"])

        def on_leave(_event: tk.Event[Any]) -> None:
            if str(btn.cget("state")) != tk.DISABLED:
                btn.configure(bg=colors["bg"])

        def on_press(_event: tk.Event[Any]) -> None:
            if str(btn.cget("state")) != tk.DISABLED:
                btn.configure(bg=colors["press"])

        def on_release(_event: tk.Event[Any]) -> None:
            if str(btn.cget("state")) != tk.DISABLED:
                btn.configure(bg=colors["hover"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<ButtonPress-1>", on_press)
        btn.bind("<ButtonRelease-1>", on_release)
        return btn

    def _make_action_handler(self, action: str) -> Callable[[], None]:
        def _handler() -> None:
            self._run_action(action)

        return _handler

    def _open_url(self, url: str) -> None:
        webbrowser.open(url)

    def _build_content(self, parent: ttk.Frame) -> None:
        content = ttk.Frame(parent, style="App.TFrame")
        content.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        notebook = ttk.Notebook(content)
        notebook.grid(row=0, column=0, sticky="nsew")

        workbench = ttk.Frame(notebook, style="Panel.TFrame", padding=12)
        history = ttk.Frame(notebook, style="Panel.TFrame", padding=12)
        lab = ttk.Frame(notebook, style="Panel.TFrame", padding=12)
        assistant = ttk.Frame(notebook, style="Panel.TFrame", padding=12)
        security = ttk.Frame(notebook, style="Panel.TFrame", padding=12)

        notebook.add(workbench, text=_tr("Workbench", "Workbench"))
        notebook.add(history, text=_tr("History", "Historial"))
        notebook.add(lab, text=_tr("Lab", "Lab"))
        notebook.add(assistant, text=_tr("Assistant", "Asistente"))
        notebook.add(security, text=_tr("Security", "Seguridad"))

        self._build_workbench_tab(workbench)
        self._build_history_tab(history)
        self._build_lab_tab(lab)
        self._build_assistant_tab(assistant)
        self._build_security_tab(security)

    def _build_workbench_tab(self, tab: ttk.Frame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        hero = ttk.LabelFrame(
            tab,
            text=_tr("Presentation", "Presentacion"),
            style="Card.TLabelframe",
            padding=10,
        )
        hero.grid(row=0, column=0, sticky="ew")
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=1)

        ttk.Label(
            hero,
            text=_tr("OCC Enterprise Desktop", "OCC Desktop Empresarial"),
            style="HeroTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            hero,
            text=_tr(
                "Claim screening, judge execution, module generation and release operations "
                "in one governed workstation.",
                "Evaluacion de claims, ejecucion de jueces, generacion de modulos y "
                "operaciones release en un solo entorno gobernado.",
            ),
            style="HeroBody.TLabel",
            wraplength=560,
            justify=tk.LEFT,
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(
            hero,
            text=_tr("Persistent SQLite run ledger enabled", "Bitacora SQLite persistente activa"),
            style="Metric.TLabel",
        ).grid(row=0, column=1, sticky="e")
        ttk.Button(
            hero,
            text=_tr("Open desktop-latest page", "Abrir pagina desktop-latest"),
            command=lambda: webbrowser.open(RELEASE_DESKTOP_ROLLING_URL),
            style="Ghost.TButton",
        ).grid(row=1, column=1, sticky="e", pady=(4, 0))

        context = ttk.LabelFrame(
            tab,
            text=_tr("Context", "Contexto"),
            style="Card.TLabelframe",
            padding=10,
        )
        context.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        for c in (1, 3):
            context.grid_columnconfigure(c, weight=1)

        ttk.Label(context, text=_tr("Workspace", "Workspace"), style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )
        ttk.Entry(context, textvariable=self.workspace_var, style="Input.TEntry").grid(
            row=0,
            column=1,
            sticky="ew",
        )
        ttk.Button(
            context,
            text=_tr("Browse", "Buscar"),
            command=self._pick_workspace,
            style="Ghost.TButton",
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(context, text=_tr("Claim file", "Archivo claim"), style="Body.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(8, 0),
        )
        ttk.Entry(context, textvariable=self.claim_var, style="Input.TEntry").grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(
            context,
            text=_tr("Browse", "Buscar"),
            command=self._pick_claim,
            style="Ghost.TButton",
        ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(context, text=_tr("Profile", "Perfil"), style="Body.TLabel").grid(
            row=0,
            column=3,
            sticky="w",
            padx=(12, 8),
        )
        ttk.Combobox(
            context,
            textvariable=self.profile_var,
            values=["core", "nuclear"],
            state="readonly",
            style="Input.TCombobox",
            width=12,
        ).grid(row=0, column=4, sticky="w")

        ttk.Label(context, text=_tr("Suite", "Suite"), style="Body.TLabel").grid(
            row=1,
            column=3,
            sticky="w",
            padx=(12, 8),
            pady=(8, 0),
        )
        ttk.Combobox(
            context,
            textvariable=self.suite_var,
            values=["canon", "extensions", "all"],
            state="readonly",
            style="Input.TCombobox",
            width=12,
        ).grid(row=1, column=4, sticky="w", pady=(8, 0))

        options = ttk.Frame(tab, style="Panel.TFrame")
        options.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        options.grid_columnconfigure(0, weight=1)

        ttk.Label(options, text=_tr("Module name", "Nombre modulo"), style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )
        ttk.Entry(options, textvariable=self.module_name_var, style="Input.TEntry", width=30).grid(
            row=0,
            column=1,
            sticky="w",
        )
        ttk.Checkbutton(
            options,
            text=_tr("Create prediction draft", "Crear borrador de prediccion"),
            variable=self.create_prediction_var,
        ).grid(row=0, column=2, sticky="w", padx=(14, 0))
        ttk.Checkbutton(
            options,
            text=_tr("Verify generated module", "Verificar modulo generado"),
            variable=self.verify_generated_var,
        ).grid(row=0, column=3, sticky="w", padx=(14, 0))

        preview = ttk.Frame(tab, style="Panel.TFrame")
        preview.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        preview.grid_columnconfigure(1, weight=1)

        ttk.Label(
            preview,
            text=_tr("Command preview", "Preview del comando"),
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Label(preview, textvariable=self.command_preview_var, style="Body.TLabel").grid(
            row=0,
            column=1,
            sticky="w",
        )
        ttk.Label(preview, text=_tr("Last run", "Ultima ejecucion"), style="Muted.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(4, 0),
        )
        ttk.Label(preview, textvariable=self.last_run_var, style="Body.TLabel").grid(
            row=1,
            column=1,
            sticky="w",
            pady=(4, 0),
        )
        ttk.Label(preview, text=_tr("Pipeline stats", "Metricas"), style="Muted.TLabel").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(4, 0),
        )
        ttk.Label(preview, textvariable=self.metrics_var, style="Muted.TLabel").grid(
            row=2,
            column=1,
            sticky="w",
            pady=(4, 0),
        )

        out_card = ttk.LabelFrame(
            tab,
            text=_tr("Output", "Salida"),
            style="Card.TLabelframe",
            padding=8,
        )
        out_card.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        out_card.grid_rowconfigure(0, weight=1)
        out_card.grid_columnconfigure(0, weight=1)

        self.output = tk.Text(
            out_card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#0b1324",
            foreground="#dbeafe",
            insertbackground="#dbeafe",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self.output.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(out_card, orient=tk.VERTICAL, command=self.output.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

        self.output.tag_configure("info", foreground="#dbeafe")
        self.output.tag_configure("command", foreground="#7dd3fc")
        self.output.tag_configure("success", foreground="#86efac")
        self.output.tag_configure("error", foreground="#fca5a5")
        self.output.tag_configure("warning", foreground="#fcd34d")

        footer = ttk.Frame(tab, style="Panel.TFrame")
        footer.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        footer.grid_columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(
            footer,
            mode="indeterminate",
            style="Status.Horizontal.TProgressbar",
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Label(footer, text=_tr("Verdict", "Veredicto"), style="Muted.TLabel").grid(
            row=0,
            column=1,
            sticky="e",
            padx=(0, 6),
        )
        self.verdict_label = ttk.Label(footer, textvariable=self.verdict_var, style="Body.TLabel")
        self.verdict_label.grid(row=0, column=2, sticky="e")

        action_row = ttk.Frame(tab, style="Panel.TFrame")
        action_row.grid(row=6, column=0, sticky="ew", pady=(8, 0))

        clear_btn = ttk.Button(
            action_row,
            text=_tr("Clear output", "Limpiar salida"),
            command=self._clear_output,
            style="Ghost.TButton",
        )
        clear_btn.pack(side=tk.LEFT)

        save_btn = ttk.Button(
            action_row,
            text=_tr("Save output", "Guardar salida"),
            command=self._save_output,
            style="Ghost.TButton",
        )
        save_btn.pack(side=tk.LEFT, padx=(8, 0))

        copy_cmd_btn = ttk.Button(
            action_row,
            text=_tr("Copy command", "Copiar comando"),
            command=self._copy_last_command,
            style="Ghost.TButton",
        )
        copy_cmd_btn.pack(side=tk.LEFT, padx=(8, 0))

    def _build_history_tab(self, tab: ttk.Frame) -> None:
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        ttk.Label(
            tab,
            text=_tr(
                "Executed commands and outcomes",
                "Comandos ejecutados y resultados",
            ),
            style="Muted.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        cols = ("time", "action", "rc", "duration", "verdict")
        self.history_tree = ttk.Treeview(tab, columns=cols, show="headings", height=16)
        self.history_tree.grid(row=1, column=0, sticky="nsew")

        self.history_tree.heading("time", text=_tr("Time", "Hora"))
        self.history_tree.heading("action", text=_tr("Action", "Accion"))
        self.history_tree.heading("rc", text="RC")
        self.history_tree.heading("duration", text=_tr("Duration", "Duracion"))
        self.history_tree.heading("verdict", text=_tr("Verdict", "Veredicto"))

        self.history_tree.column("time", width=180, anchor=tk.W)
        self.history_tree.column("action", width=180, anchor=tk.W)
        self.history_tree.column("rc", width=60, anchor=tk.CENTER)
        self.history_tree.column("duration", width=100, anchor=tk.E)
        self.history_tree.column("verdict", width=160, anchor=tk.W)

        self.history_tree.bind("<Double-1>", self._rerun_selected_history)

        actions = ttk.Frame(tab, style="Panel.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        ttk.Button(
            actions,
            text=_tr("Rerun selected", "Re-ejecutar seleccionado"),
            command=self._rerun_selected_history,
            style="Primary.TButton",
        ).pack(side=tk.LEFT)
        ttk.Button(
            actions,
            text=_tr("Copy selected command", "Copiar comando seleccionado"),
            command=self._copy_selected_history_command,
            style="Ghost.TButton",
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            actions,
            text=_tr("Export CSV", "Exportar CSV"),
            command=self._export_history_csv,
            style="Ghost.TButton",
        ).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(
            actions,
            text=_tr("Clear history", "Limpiar historial"),
            command=self._clear_history,
            style="Ghost.TButton",
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _build_lab_tab(self, tab: ttk.Frame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        intro = ttk.LabelFrame(
            tab,
            text=_tr("Experiment Lab", "Experiment Lab"),
            style="Card.TLabelframe",
            padding=10,
        )
        intro.grid(row=0, column=0, sticky="ew")
        intro.grid_columnconfigure(1, weight=1)

        ttk.Label(intro, text=_tr("Claims folder", "Carpeta de claims"), style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )
        ttk.Entry(intro, textvariable=self.lab_claims_dir_var, style="Input.TEntry").grid(
            row=0,
            column=1,
            sticky="ew",
        )
        ttk.Button(
            intro,
            text=_tr("Browse", "Buscar"),
            command=self._pick_lab_claims_dir,
            style="Ghost.TButton",
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(intro, text=_tr("Output folder", "Carpeta de salida"), style="Body.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(8, 0),
        )
        ttk.Entry(intro, textvariable=self.lab_out_dir_var, style="Input.TEntry").grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(
            intro,
            text=_tr("Browse", "Buscar"),
            command=self._pick_lab_out_dir,
            style="Ghost.TButton",
        ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))

        options = ttk.Frame(tab, style="Panel.TFrame")
        options.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ttk.Checkbutton(
            options,
            text=_tr("Core profile", "Perfil core"),
            variable=self.lab_profile_core_var,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            options,
            text=_tr("Nuclear profile", "Perfil nuclear"),
            variable=self.lab_profile_nuclear_var,
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Checkbutton(
            options,
            text=_tr("Recursive scan", "Escaneo recursivo"),
            variable=self.lab_recursive_var,
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Checkbutton(
            options,
            text=_tr("Strict trace", "Trace estricto"),
            variable=self.lab_strict_trace_var,
        ).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Checkbutton(
            options,
            text=_tr("Fail on non-pass", "Fallar en no-pass"),
            variable=self.lab_fail_on_non_pass_var,
        ).pack(side=tk.LEFT, padx=(12, 0))

        controls = ttk.Frame(tab, style="Panel.TFrame")
        controls.grid(row=2, column=0, sticky="ew", pady=(8, 0))

        run_btn = self._create_modern_button(
            controls,
            label=_tr("Run lab matrix", "Ejecutar matriz lab"),
            command=lambda: self._run_action("lab_run"),
            variant="primary",
        )
        run_btn.pack(side=tk.LEFT)
        self._buttons.append(run_btn)

        open_btn = self._create_modern_button(
            controls,
            label=_tr("Open output folder", "Abrir carpeta salida"),
            command=self._open_lab_output_folder,
            variant="ghost",
        )
        open_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._buttons.append(open_btn)

        ttk.Label(
            controls,
            textvariable=self.lab_status_var,
            style="Muted.TLabel",
        ).pack(side=tk.LEFT, padx=(14, 0))

        metrics = ttk.Frame(tab, style="Panel.TFrame")
        metrics.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        for idx in range(10):
            metrics.grid_columnconfigure(idx, weight=0)
        metrics.grid_columnconfigure(9, weight=1)

        ttk.Label(metrics, text="Runs", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(metrics, textvariable=self.lab_runs_var, style="Metric.TLabel").grid(
            row=0,
            column=1,
            sticky="w",
            padx=(6, 18),
        )
        ttk.Label(metrics, text="PASS", style="Muted.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Label(metrics, textvariable=self.lab_pass_var, style="Metric.TLabel").grid(
            row=0,
            column=3,
            sticky="w",
            padx=(6, 18),
        )
        ttk.Label(metrics, text="FAIL", style="Muted.TLabel").grid(row=0, column=4, sticky="w")
        ttk.Label(metrics, textvariable=self.lab_fail_var, style="Metric.TLabel").grid(
            row=0,
            column=5,
            sticky="w",
            padx=(6, 18),
        )
        ttk.Label(metrics, text="NO-EVAL", style="Muted.TLabel").grid(
            row=0,
            column=6,
            sticky="w",
        )
        ttk.Label(metrics, textvariable=self.lab_no_eval_var, style="Metric.TLabel").grid(
            row=0,
            column=7,
            sticky="w",
            padx=(6, 18),
        )
        ttk.Label(metrics, text=_tr("Divergence", "Divergencia"), style="Muted.TLabel").grid(
            row=0,
            column=8,
            sticky="w",
        )
        ttk.Label(metrics, textvariable=self.lab_divergence_var, style="Metric.TLabel").grid(
            row=0,
            column=9,
            sticky="w",
            padx=(6, 0),
        )

        out_card = ttk.LabelFrame(
            tab,
            text=_tr("Lab output", "Salida del lab"),
            style="Card.TLabelframe",
            padding=8,
        )
        out_card.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        out_card.grid_rowconfigure(0, weight=1)
        out_card.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        self._lab_output_text = tk.Text(
            out_card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#031124",
            foreground="#bfdbfe",
            insertbackground="#bfdbfe",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self._lab_output_text.grid(row=0, column=0, sticky="nsew")
        self._lab_output_text.tag_configure("meta", foreground="#7dd3fc")
        self._lab_output_text.tag_configure("warn", foreground="#fcd34d")
        self._lab_output_text.tag_configure("error", foreground="#fca5a5")

        lab_scroll = ttk.Scrollbar(
            out_card,
            orient=tk.VERTICAL,
            command=self._lab_output_text.yview,
        )
        lab_scroll.grid(row=0, column=1, sticky="ns")
        self._lab_output_text.configure(yscrollcommand=lab_scroll.set)

    def _build_assistant_tab(self, tab: ttk.Frame) -> None:
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        intro = ttk.LabelFrame(
            tab,
            text=_tr("AI assistant", "Asistente IA"),
            style="Card.TLabelframe",
            padding=10,
        )
        intro.grid(row=0, column=0, sticky="ew")
        intro.grid_columnconfigure(1, weight=1)
        intro.grid_columnconfigure(3, weight=1)

        ttk.Label(intro, text=_tr("Provider", "Proveedor"), style="Body.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
        )
        ttk.Combobox(
            intro,
            textvariable=self.ai_provider_var,
            values=["offline", "openai"],
            state="readonly",
            style="Input.TCombobox",
            width=14,
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(intro, text=_tr("Model", "Modelo"), style="Body.TLabel").grid(
            row=0,
            column=2,
            sticky="w",
            padx=(14, 8),
        )
        ttk.Entry(intro, textvariable=self.ai_model_var, style="Input.TEntry").grid(
            row=0,
            column=3,
            sticky="ew",
        )

        ttk.Label(intro, text=_tr("Timeout (s)", "Timeout (s)"), style="Body.TLabel").grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(8, 0),
        )
        ttk.Entry(intro, textvariable=self.ai_timeout_var, style="Input.TEntry", width=10).grid(
            row=1,
            column=1,
            sticky="w",
            pady=(8, 0),
        )

        ttk.Checkbutton(
            intro,
            text=_tr("Include runtime context", "Incluir contexto del runtime"),
            variable=self.ai_include_context_var,
        ).grid(row=1, column=2, columnspan=2, sticky="w", padx=(14, 0), pady=(8, 0))

        ttk.Label(intro, text=_tr("API key", "API key"), style="Body.TLabel").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(8, 0),
        )
        key_entry = ttk.Entry(
            intro,
            textvariable=self._assistant_api_key_var,
            style="Input.TEntry",
            show="*",
        )
        key_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(
            intro,
            text=_tr("Set from env", "Tomar de env"),
            command=self._set_api_key_from_env,
            style="Ghost.TButton",
        ).grid(row=2, column=3, sticky="e", pady=(8, 0))

        ttk.Label(
            tab,
            textvariable=self.assistant_status_var,
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        prompt_card = ttk.LabelFrame(
            tab,
            text=_tr("Prompt", "Prompt"),
            style="Card.TLabelframe",
            padding=8,
        )
        prompt_card.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        prompt_card.grid_columnconfigure(0, weight=1)

        self._assistant_prompt_text = tk.Text(
            prompt_card,
            height=6,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            background="#0b1324",
            foreground="#e2e8f0",
            insertbackground="#e2e8f0",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self._assistant_prompt_text.grid(row=0, column=0, sticky="ew")

        controls = ttk.Frame(prompt_card, style="Panel.TFrame")
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self._assistant_send_button = self._create_modern_button(
            controls,
            label=_tr("Ask assistant", "Preguntar asistente"),
            command=self._ask_assistant,
            variant="primary",
        )
        self._assistant_send_button.pack(side=tk.LEFT)

        self._assistant_clear_button = self._create_modern_button(
            controls,
            label=_tr("Clear", "Limpiar"),
            command=self._clear_assistant_prompt,
            variant="ghost",
        )
        self._assistant_clear_button.pack(side=tk.LEFT, padx=(8, 0))

        self._assistant_copy_button = self._create_modern_button(
            controls,
            label=_tr("Copy last reply", "Copiar ultima respuesta"),
            command=self._copy_assistant_reply,
            variant="ghost",
        )
        self._assistant_copy_button.pack(side=tk.LEFT, padx=(8, 0))

        system_card = ttk.LabelFrame(
            tab,
            text=_tr("System prompt", "Prompt del sistema"),
            style="Card.TLabelframe",
            padding=8,
        )
        system_card.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        system_card.grid_columnconfigure(0, weight=1)

        self._assistant_system_text = tk.Text(
            system_card,
            height=3,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            background="#0b1324",
            foreground="#93c5fd",
            insertbackground="#93c5fd",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self._assistant_system_text.grid(row=0, column=0, sticky="ew")
        self._assistant_system_text.insert("1.0", self.ai_system_prompt_var.get())

        output_card = ttk.LabelFrame(
            tab,
            text=_tr("Assistant output", "Salida del asistente"),
            style="Card.TLabelframe",
            padding=8,
        )
        output_card.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        output_card.grid_columnconfigure(0, weight=1)
        output_card.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        self._assistant_output_text = tk.Text(
            output_card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            background="#030b1d",
            foreground="#dbeafe",
            insertbackground="#dbeafe",
            relief=tk.FLAT,
            borderwidth=0,
        )
        self._assistant_output_text.grid(row=0, column=0, sticky="nsew")
        self._assistant_output_text.tag_configure("assistant", foreground="#bfdbfe")
        self._assistant_output_text.tag_configure("error", foreground="#fca5a5")
        self._assistant_output_text.tag_configure("meta", foreground="#7dd3fc")

        assistant_scroll = ttk.Scrollbar(
            output_card,
            orient=tk.VERTICAL,
            command=self._assistant_output_text.yview,
        )
        assistant_scroll.grid(row=0, column=1, sticky="ns")
        self._assistant_output_text.configure(yscrollcommand=assistant_scroll.set)

    def _build_security_tab(self, tab: ttk.Frame) -> None:
        tab.grid_columnconfigure(0, weight=1)

        ttk.Label(
            tab,
            text=_tr("Security and distribution", "Seguridad y distribucion"),
            style="CardTitle.TLabel",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            tab,
            text=_tr(
                "To reduce Windows SmartScreen warnings, publish signed binaries with a "
                "trusted code "
                "signing certificate, timestamp signatures, and distribute via official "
                "releases.",
                "Para reducir avisos de SmartScreen, publica binarios firmados con certificado "
                "de firma confiable, agrega timestamp y distribuye por releases oficiales.",
            ),
            style="Body.TLabel",
            wraplength=840,
            justify=tk.LEFT,
        ).grid(row=1, column=0, sticky="w", pady=(8, 12))

        link_frame = ttk.Frame(tab, style="Panel.TFrame")
        link_frame.grid(row=2, column=0, sticky="w")

        ttk.Button(
            link_frame,
            text=_tr("Download Setup installer", "Descargar instalador Setup"),
            command=lambda: webbrowser.open(
                RELEASE_DESKTOP_ROLLING_BASE + "OCCDesktop-Setup-windows-x64.exe"
            ),
            style="Primary.TButton",
        ).pack(side=tk.LEFT)

        ttk.Button(
            tab,
            text=_tr(
                "Check local EXE Authenticode signature",
                "Verificar firma Authenticode local",
            ),
            command=self._check_local_signature,
            style="Ghost.TButton",
        ).grid(row=3, column=0, sticky="w", pady=(16, 0))

        ttk.Label(
            tab,
            text=_tr(
                "Tip: SmartScreen reputation is reputation-based. "
                "Even validly signed new files may "
                "still show warnings until reputation builds.",
                "Tip: SmartScreen se basa en reputacion. Incluso archivos nuevos firmados pueden "
                "mostrar aviso hasta acumular reputacion.",
            ),
            style="Muted.TLabel",
            wraplength=840,
            justify=tk.LEFT,
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-Return>", lambda _e: self._run_action("judge"))
        self.bind("<Control-l>", lambda _e: self._clear_output())
        self.bind("<Control-s>", lambda _e: self._save_output())

    def _load_settings(self) -> None:
        try:
            if not self.settings_file.is_file():
                return
            raw = json.loads(self.settings_file.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return

            def _set_str(var: tk.StringVar, key: str) -> None:
                val = raw.get(key)
                if isinstance(val, str) and val.strip():
                    var.set(val)

            def _set_bool(var: tk.BooleanVar, key: str) -> None:
                val = raw.get(key)
                if isinstance(val, bool):
                    var.set(val)

            _set_str(self.workspace_var, "workspace")
            _set_str(self.claim_var, "claim")
            _set_str(self.profile_var, "profile")
            _set_str(self.suite_var, "suite")
            _set_str(self.module_name_var, "module_name")
            _set_bool(self.create_prediction_var, "create_prediction")
            _set_bool(self.verify_generated_var, "verify_generated")
            _set_str(self.ai_provider_var, "ai_provider")
            _set_str(self.ai_model_var, "ai_model")
            _set_str(self.ai_timeout_var, "ai_timeout")
            _set_bool(self.ai_include_context_var, "ai_include_context")
            _set_str(self.ai_system_prompt_var, "ai_system_prompt")
            _set_str(self.lab_claims_dir_var, "lab_claims_dir")
            _set_str(self.lab_out_dir_var, "lab_out_dir")
            _set_bool(self.lab_recursive_var, "lab_recursive")
            _set_bool(self.lab_profile_core_var, "lab_profile_core")
            _set_bool(self.lab_profile_nuclear_var, "lab_profile_nuclear")
            _set_bool(self.lab_strict_trace_var, "lab_strict_trace")
            _set_bool(self.lab_fail_on_non_pass_var, "lab_fail_on_non_pass")
        except Exception:
            pass

    def _save_settings(self) -> None:
        system_prompt = self.ai_system_prompt_var.get().strip()
        if self._assistant_system_text is not None:
            system_prompt = self._assistant_system_text.get("1.0", tk.END).strip()
            self.ai_system_prompt_var.set(system_prompt)
        payload = {
            "workspace": self.workspace_var.get().strip(),
            "claim": self.claim_var.get().strip(),
            "profile": self.profile_var.get().strip(),
            "suite": self.suite_var.get().strip(),
            "module_name": self.module_name_var.get().strip(),
            "create_prediction": bool(self.create_prediction_var.get()),
            "verify_generated": bool(self.verify_generated_var.get()),
            "ai_provider": self.ai_provider_var.get().strip(),
            "ai_model": self.ai_model_var.get().strip(),
            "ai_timeout": self.ai_timeout_var.get().strip(),
            "ai_include_context": bool(self.ai_include_context_var.get()),
            "ai_system_prompt": system_prompt,
            "lab_claims_dir": self.lab_claims_dir_var.get().strip(),
            "lab_out_dir": self.lab_out_dir_var.get().strip(),
            "lab_recursive": bool(self.lab_recursive_var.get()),
            "lab_profile_core": bool(self.lab_profile_core_var.get()),
            "lab_profile_nuclear": bool(self.lab_profile_nuclear_var.get()),
            "lab_strict_trace": bool(self.lab_strict_trace_var.get()),
            "lab_fail_on_non_pass": bool(self.lab_fail_on_non_pass_var.get()),
        }
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _on_close(self) -> None:
        self._save_settings()
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        if self._db_conn is not None:
            try:
                self._db_conn.close()
            except Exception:
                pass
        self.destroy()

    def _workspace(self) -> Optional[Path]:
        raw = self.workspace_var.get().strip()
        if not raw:
            messagebox.showerror(
                "OCC Desktop",
                _tr("Workspace is required.", "Workspace es obligatorio."),
            )
            return None
        path = Path(raw).resolve()
        if not path.is_dir():
            messagebox.showerror(
                "OCC Desktop",
                _tr("Workspace folder does not exist.", "La carpeta workspace no existe."),
            )
            return None
        return path

    def _claim(self) -> Optional[Path]:
        raw = self.claim_var.get().strip()
        if not raw:
            messagebox.showerror(
                "OCC Desktop",
                _tr("Claim file is required.", "El claim es obligatorio."),
            )
            return None
        path = Path(raw).resolve()
        if not path.is_file():
            messagebox.showerror(
                "OCC Desktop",
                _tr("Claim file does not exist.", "El archivo claim no existe."),
            )
            return None
        return path

    def _pick_workspace(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.workspace_var.get() or ".")
        if selected:
            self.workspace_var.set(str(Path(selected).resolve()))

    def _pick_claim(self) -> None:
        selected = filedialog.askopenfilename(
            initialdir=str(Path(self.workspace_var.get() or ".").resolve()),
            filetypes=[
                (_tr("Claim files", "Archivos claim"), "*.yaml *.yml *.json"),
                (_tr("All files", "Todos"), "*.*"),
            ],
        )
        if selected:
            self.claim_var.set(str(Path(selected).resolve()))

    def _pick_lab_claims_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.lab_claims_dir_var.get() or ".")
        if selected:
            self.lab_claims_dir_var.set(str(Path(selected).resolve()))

    def _pick_lab_out_dir(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.lab_out_dir_var.get() or ".")
        if selected:
            self.lab_out_dir_var.set(str(Path(selected).resolve()))

    def _open_lab_output_folder(self) -> None:
        out_dir = Path(self.lab_out_dir_var.get().strip() or ".").resolve()
        if not out_dir.exists():
            messagebox.showwarning(
                "OCC Desktop",
                _tr(
                    f"Lab output folder does not exist yet: {out_dir}",
                    f"La carpeta de salida del lab no existe todavia: {out_dir}",
                ),
            )
            return

        if os.name == "nt":
            os.startfile(str(out_dir))  # type: ignore[attr-defined]
            return
        webbrowser.open(out_dir.as_uri())

    def _load_lab_report(self, path: Path) -> None:
        if not path.is_file():
            self.lab_status_var.set(_tr("Lab report not found", "Reporte lab no encontrado"))
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            self.lab_status_var.set(_tr(f"Lab report parse error: {e}", f"Error parse lab: {e}"))
            return

        totals = payload.get("totals", {}) if isinstance(payload, dict) else {}
        self.lab_runs_var.set(str(int(totals.get("runs", 0))))
        self.lab_pass_var.set(str(int(totals.get("pass", 0))))
        self.lab_fail_var.set(str(int(totals.get("fail", 0))))
        self.lab_no_eval_var.set(str(int(totals.get("no_eval", 0))))
        self.lab_divergence_var.set(str(int(payload.get("divergence_count", 0))))
        self.lab_status_var.set(_tr("Lab report loaded", "Reporte lab cargado"))

        if self._lab_output_text is None:
            return
        self._lab_output_text.delete("1.0", tk.END)
        self._lab_output_text.insert(
            tk.END,
            f"[{_now_text()}] lab_report.json\n",
            "meta",
        )
        self._lab_output_text.insert(
            tk.END,
            _tr(
                f"Runs: {self.lab_runs_var.get()} | PASS: {self.lab_pass_var.get()} | "
                f"FAIL: {self.lab_fail_var.get()} | NO-EVAL: {self.lab_no_eval_var.get()} | "
                f"Divergence: {self.lab_divergence_var.get()}\n\n",
                f"Ejecuciones: {self.lab_runs_var.get()} | PASS: {self.lab_pass_var.get()} | "
                f"FAIL: {self.lab_fail_var.get()} | NO-EVAL: {self.lab_no_eval_var.get()} | "
                f"Divergencia: {self.lab_divergence_var.get()}\n\n",
            ),
        )
        divergence = payload.get("divergence", [])
        if isinstance(divergence, list) and divergence:
            self._lab_output_text.insert(
                tk.END,
                _tr("Diverging claims:\n", "Claims divergentes:\n"),
                "warn",
            )
            for row in divergence[:20]:
                if not isinstance(row, dict):
                    continue
                claim_id = str(row.get("claim_id") or "unknown")
                profiles = row.get("profiles", [])
                parts: List[str] = []
                if isinstance(profiles, list):
                    for item in profiles:
                        if not isinstance(item, dict):
                            continue
                        parts.append(
                            f"{item.get('profile', '')}:{item.get('verdict', '')}"
                        )
                self._lab_output_text.insert(
                    tk.END,
                    f"- {claim_id} -> {', '.join(parts)}\n",
                )
        else:
            self._lab_output_text.insert(
                tk.END,
                _tr(
                    "No profile divergence detected in this matrix.",
                    "No se detecto divergencia de perfiles en esta matriz.",
                ),
                "meta",
            )
        self._lab_output_text.see(tk.END)

    def _set_api_key_from_env(self) -> None:
        key = str(os.getenv("OPENAI_API_KEY") or "").strip()
        if not key:
            messagebox.showwarning(
                "OCC Desktop",
                _tr(
                    "OPENAI_API_KEY is not set in this environment.",
                    "OPENAI_API_KEY no esta definido en este entorno.",
                ),
            )
            return
        self._assistant_api_key_var.set(key)
        self.assistant_status_var.set(
            _tr("API key loaded from environment", "API key cargada desde entorno")
        )

    def _show_set_api_key_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("OPENAI_API_KEY")
        dialog.configure(bg=self.BG)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Label(
            dialog,
            text=_tr(
                "Paste your OpenAI API key (stored only for this app session).",
                "Pega tu API key de OpenAI (solo se guarda en esta sesion).",
            ),
            style="SubHeader.TLabel",
            wraplength=460,
            justify=tk.LEFT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        key_var = tk.StringVar(value=self._assistant_api_key_var.get())
        entry = ttk.Entry(dialog, textvariable=key_var, style="Input.TEntry", show="*")
        entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14)
        entry.focus_set()

        def save_key() -> None:
            self._assistant_api_key_var.set(key_var.get().strip())
            self.assistant_status_var.set(
                _tr("API key updated (session only)", "API key actualizada (solo sesion)")
            )
            dialog.destroy()

        ttk.Button(
            dialog,
            text=_tr("Cancel", "Cancelar"),
            command=dialog.destroy,
            style="Ghost.TButton",
        ).grid(row=2, column=0, sticky="w", padx=14, pady=12)
        ttk.Button(
            dialog,
            text=_tr("Save", "Guardar"),
            command=save_key,
            style="Primary.TButton",
        ).grid(row=2, column=1, sticky="e", padx=14, pady=12)

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_columnconfigure(1, weight=1)

    def _clear_assistant_prompt(self) -> None:
        if self._assistant_prompt_text is None:
            return
        self._assistant_prompt_text.delete("1.0", tk.END)

    def _copy_assistant_reply(self) -> None:
        if not self._assistant_last_reply.strip():
            return
        self.clipboard_clear()
        self.clipboard_append(self._assistant_last_reply)
        self.assistant_status_var.set(
            _tr("Assistant reply copied", "Respuesta del asistente copiada")
        )

    def _set_assistant_busy(self, busy: bool) -> None:
        self._assistant_running = busy
        for widget in (self._assistant_send_button, self._assistant_clear_button):
            if widget is not None:
                if busy:
                    widget.configure(state=tk.DISABLED)
                else:
                    widget.configure(state=tk.NORMAL)

    def _collect_assistant_context(self) -> str:
        lines = [
            f"Version: {self.version_var.get()}",
            f"Profile: {self.profile_var.get().strip() or 'core'}",
            f"Suite: {self.suite_var.get().strip() or 'extensions'}",
            f"Workspace: {self.workspace_var.get().strip()}",
            f"Claim: {self.claim_var.get().strip()}",
            f"Last command: {self.command_preview_var.get().strip()}",
            f"Last run: {self.last_run_var.get().strip()}",
            f"Stats: {self.metrics_var.get().strip()}",
        ]
        if self._run_log_buffer:
            tail = "".join(self._run_log_buffer)[-2000:].strip()
            if tail:
                lines.append("Recent output tail:")
                lines.append(tail)
        return "\n".join(lines).strip()

    def _ask_assistant(self) -> None:
        if self._assistant_running:
            return
        if self._assistant_prompt_text is None:
            return
        prompt = self._assistant_prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning(
                "OCC Desktop",
                _tr("Assistant prompt is empty.", "El prompt del asistente esta vacio."),
            )
            return

        provider = self.ai_provider_var.get().strip().lower() or "offline"
        if provider not in {"offline", "openai"}:
            messagebox.showwarning(
                "OCC Desktop",
                _tr(
                    "Unsupported assistant provider.",
                    "Proveedor de asistente no soportado.",
                ),
            )
            return

        timeout_raw = self.ai_timeout_var.get().strip()
        try:
            timeout_s = max(5, min(180, int(timeout_raw)))
        except ValueError:
            timeout_s = 45
        self.ai_timeout_var.set(str(timeout_s))

        system_prompt = self.ai_system_prompt_var.get().strip()
        if self._assistant_system_text is not None:
            system_prompt = self._assistant_system_text.get("1.0", tk.END).strip()
        self.ai_system_prompt_var.set(system_prompt)

        full_prompt = prompt
        if self.ai_include_context_var.get():
            full_prompt = (
                f"{prompt}\n\n[OCC runtime context]\n"
                f"{self._collect_assistant_context()}\n[/OCC runtime context]"
            )

        model = self.ai_model_var.get().strip() or "gpt-4.1-mini"
        api_key = self._assistant_api_key_var.get().strip()
        self._set_assistant_busy(True)
        if provider == "offline":
            self.assistant_status_var.set(
                _tr("Running offline assistant...", "Ejecutando asistente offline...")
            )
        else:
            self.assistant_status_var.set(
                _tr("Calling OpenAI assistant...", "Consultando asistente OpenAI...")
            )
        if self._assistant_output_text is not None:
            self._assistant_output_text.insert(
                tk.END,
                f"\n[{_now_text()}] {provider}:{model}\n",
                "meta",
            )
            self._assistant_output_text.insert(
                tk.END,
                f"{_tr('You: ', 'Tu: ')}{prompt}\n\n",
                "meta",
            )
            self._assistant_output_text.see(tk.END)

        def worker() -> None:
            try:
                if provider == "offline":
                    reply = ask_offline(prompt=prompt, context=full_prompt)
                else:
                    reply = ask_openai(
                        prompt=full_prompt,
                        model=model,
                        api_key=api_key or None,
                        system_prompt=system_prompt,
                        timeout_s=timeout_s,
                    )
                self._queue.put(("assistant_done", {"reply": reply}))
            except AssistantError as e:
                self._queue.put(("assistant_error", {"error": str(e)}))
            except Exception as e:
                self._queue.put(("assistant_error", {"error": str(e)}))

        threading.Thread(target=worker, daemon=True).start()

    def _resolve_script(self, script_name: str) -> Path:
        workspace = Path(self.workspace_var.get()).resolve()
        candidate = workspace / "scripts" / script_name
        if candidate.is_file():
            return candidate
        return self.repo_root / "scripts" / script_name

    def _set_running(self, running: bool) -> None:
        self._running = running
        for button in self._buttons:
            if str(button.cget("text")) == _tr("Stop running command", "Detener comando"):
                continue
            button.configure(state=tk.DISABLED if running else tk.NORMAL)
        if running:
            self.progress.start(8)
        else:
            self.progress.stop()

    def _append_output(self, text: str, tag: str = "info") -> None:
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)

    def _clear_output(self) -> None:
        self.output.delete("1.0", tk.END)

    def _save_output(self) -> None:
        selected = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[(_tr("Log files", "Archivos log"), "*.log"), (_tr("All", "Todos"), "*.*")],
        )
        if not selected:
            return
        Path(selected).write_text(self.output.get("1.0", tk.END), encoding="utf-8")
        self.status_var.set(_tr("Output saved", "Salida guardada"))

    def _copy_last_command(self) -> None:
        if not self._last_cmd:
            return
        cmd_text = _fmt_cmd(self._last_cmd)
        self.clipboard_clear()
        self.clipboard_append(cmd_text)
        self.status_var.set(_tr("Command copied", "Comando copiado"))

    def _record_history(
        self,
        started_at: str,
        action: str,
        rc: int,
        duration_s: float,
        verdict: str,
        command: Sequence[str],
        output_excerpt: str,
    ) -> None:
        db_id = self._persist_history_row(
            started_at=started_at,
            action=action,
            rc=rc,
            duration_s=duration_s,
            verdict=verdict,
            command=command,
            output_excerpt=output_excerpt,
        )
        self._insert_history_row(
            started_at=started_at,
            action=action,
            rc=rc,
            duration_s=duration_s,
            verdict=verdict,
            command=command,
            db_id=db_id,
        )
        self._update_stats(action, rc, duration_s, verdict)

    def _insert_history_row(
        self,
        started_at: str,
        action: str,
        rc: int,
        duration_s: float,
        verdict: str,
        command: Sequence[str],
        db_id: Optional[int],
    ) -> None:
        iid = self.history_tree.insert(
            "",
            tk.END,
            values=(
                started_at,
                action,
                rc,
                f"{duration_s:.2f}s",
                verdict or "-",
            ),
        )
        self._history_commands[str(iid)] = list(command)
        if db_id is not None:
            self._history_db_ids[str(iid)] = db_id

    def _refresh_stats_from_tree(self) -> None:
        rows = list(self.history_tree.get_children())
        self._stats_total_runs = len(rows)
        self._stats_pass = 0
        self._stats_fail = 0
        self._stats_no_eval = 0

        for iid in rows:
            values = self.history_tree.item(iid).get("values", [])
            verdict_text = str(values[4] if len(values) >= 5 else "")
            norm = verdict_text.upper()
            if norm.startswith("PASS"):
                self._stats_pass += 1
            elif norm.startswith("FAIL"):
                self._stats_fail += 1
            elif norm.startswith("NO-EVAL"):
                self._stats_no_eval += 1

        self.metrics_var.set(
            _tr(
                f"Runs: {self._stats_total_runs} | PASS: {self._stats_pass} | "
                f"FAIL: {self._stats_fail} | NO-EVAL: {self._stats_no_eval}",
                f"Ejecuciones: {self._stats_total_runs} | PASS: {self._stats_pass} | "
                f"FAIL: {self._stats_fail} | NO-EVAL: {self._stats_no_eval}",
            )
        )

    def _update_stats(self, action: str, rc: int, duration_s: float, verdict: str) -> None:
        self._stats_total_runs += 1
        normalized = verdict.upper().strip()
        if normalized.startswith("PASS"):
            self._stats_pass += 1
        elif normalized.startswith("FAIL"):
            self._stats_fail += 1
        elif normalized.startswith("NO-EVAL"):
            self._stats_no_eval += 1

        self.last_run_var.set(
            _tr(
                f"{action} | exit {rc} | {duration_s:.2f}s | {verdict or '-'}",
                f"{action} | salida {rc} | {duration_s:.2f}s | {verdict or '-'}",
            )
        )
        self.metrics_var.set(
            _tr(
                f"Runs: {self._stats_total_runs} | PASS: {self._stats_pass} | "
                f"FAIL: {self._stats_fail} | NO-EVAL: {self._stats_no_eval}",
                f"Ejecuciones: {self._stats_total_runs} | PASS: {self._stats_pass} | "
                f"FAIL: {self._stats_fail} | NO-EVAL: {self._stats_no_eval}",
            )
        )

    def _export_history_csv(self) -> None:
        selected = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), (_tr("All", "Todos"), "*.*")],
            title=_tr("Export history to CSV", "Exportar historial a CSV"),
        )
        if not selected:
            return

        rows = self.history_tree.get_children()
        with Path(selected).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time", "action", "rc", "duration", "verdict", "command"])
            for iid in rows:
                values = self.history_tree.item(iid).get("values", [])
                command = _fmt_cmd(self._history_commands.get(str(iid), []))
                writer.writerow(list(values) + [command])

        self.status_var.set(_tr("History CSV exported", "Historial exportado a CSV"))

    def _clear_history(self) -> None:
        ok = messagebox.askyesno(
            "OCC Desktop",
            _tr(
                "Delete all persisted run history from this workstation?",
                "Eliminar todo el historial persistente de esta estacion?",
            ),
        )
        if not ok:
            return

        for iid in self.history_tree.get_children():
            self.history_tree.delete(iid)
        self._history_commands.clear()
        self._history_db_ids.clear()

        if self._db_conn is not None:
            try:
                self._db_conn.execute("DELETE FROM run_history")
                self._db_conn.commit()
            except Exception:
                pass

        self.last_run_var.set("-")
        self._refresh_stats_from_tree()
        self.status_var.set(_tr("History cleared", "Historial limpiado"))

    def _rerun_selected_history(self, _event: Optional[tk.Event[Any]] = None) -> None:
        selected = self.history_tree.selection()
        if not selected:
            return
        iid = str(selected[0])
        cmd = self._history_commands.get(iid)
        if not cmd:
            return
        rerun_cmd = list(cmd)
        if len(rerun_cmd) == 1 and " " in rerun_cmd[0]:
            try:
                rerun_cmd = shlex.split(rerun_cmd[0])
            except Exception:
                pass
        self._start_command("history-rerun", rerun_cmd)

    def _copy_selected_history_command(self) -> None:
        selected = self.history_tree.selection()
        if not selected:
            return
        cmd = self._history_commands.get(str(selected[0]))
        if not cmd:
            return
        self.clipboard_clear()
        self.clipboard_append(_fmt_cmd(cmd))
        self.status_var.set(_tr("History command copied", "Comando del historial copiado"))

    def _start_command(self, label: str, cmd: Sequence[str]) -> None:
        if self._running:
            messagebox.showwarning(
                "OCC Desktop",
                _tr("A command is already running.", "Ya hay un comando ejecutandose."),
            )
            return

        workspace = self._workspace()
        if workspace is None:
            return

        self._running_label = label
        self._running_started_at = time.monotonic()
        self._running_started_text = _now_text()
        self._current_verdict = ""
        self._last_cmd = list(cmd)
        self._run_log_buffer = []
        self.verdict_var.set("-")

        cmd_text = _fmt_cmd(cmd)
        self.command_preview_var.set(cmd_text)

        self._set_running(True)
        self.status_var.set(_tr(f"Running: {label}", f"Ejecutando: {label}"))
        if label == "lab-run":
            self.lab_status_var.set(_tr("Running lab matrix...", "Ejecutando matriz lab..."))
        self._append_output("\n" + "=" * 88 + "\n", "command")
        self._append_output(f"[{self._running_started_text}] $ {cmd_text}\n\n", "command")

        def worker() -> None:
            try:
                proc = subprocess.Popen(
                    list(cmd),
                    cwd=workspace,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                self._proc = proc
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._queue.put(("line", {"text": line}))
                rc = int(proc.wait())
                duration = time.monotonic() - self._running_started_at
                self._queue.put(("done", {"rc": rc, "duration": duration, "label": label}))
            except Exception as e:
                self._queue.put(("line", {"text": f"[ERROR] {e}\n"}))
                self._queue.put(("done", {"rc": -1, "duration": 0.0, "label": label}))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_queue(self) -> None:
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break

            if kind == "line":
                text = str(payload.get("text") or "")
                self._handle_output_line(text)
            elif kind == "done":
                self._proc = None
                self._set_running(False)

                rc = int(payload.get("rc") or -1)
                duration = float(payload.get("duration") or 0.0)
                label = str(payload.get("label") or self._running_label)
                verdict = self._current_verdict

                output_excerpt = "".join(self._run_log_buffer)[-8000:]
                self._record_history(
                    started_at=self._running_started_text,
                    action=label,
                    rc=rc,
                    duration_s=duration,
                    verdict=verdict,
                    command=self._last_cmd,
                    output_excerpt=output_excerpt,
                )

                if rc == 0:
                    self.status_var.set(_tr("Done (exit 0)", "Terminado (salida 0)"))
                    self._append_output(f"\n[exit {rc}]\n", "success")
                else:
                    self.status_var.set(
                        _tr(f"Finished with exit {rc}", f"Terminado con salida {rc}")
                    )
                    self._append_output(f"\n[exit {rc}]\n", "error")

                if label == "lab-run":
                    report_path = (
                        Path(self.lab_out_dir_var.get().strip() or ".") / "lab_report.json"
                    )
                    self._load_lab_report(report_path)
            elif kind == "assistant_done":
                reply = str(payload.get("reply") or "")
                self._assistant_last_reply = reply
                self._set_assistant_busy(False)
                self.assistant_status_var.set(_tr("Assistant ready", "Asistente listo"))
                if self._assistant_output_text is not None:
                    self._assistant_output_text.insert(
                        tk.END,
                        f"{_tr('Assistant: ', 'Asistente: ')}{reply}\n\n",
                        "assistant",
                    )
                    self._assistant_output_text.see(tk.END)
            elif kind == "assistant_error":
                message = str(payload.get("error") or "unknown error")
                self._set_assistant_busy(False)
                self.assistant_status_var.set(
                    _tr("Assistant request failed", "Fallo en solicitud del asistente")
                )
                if self._assistant_output_text is not None:
                    self._assistant_output_text.insert(
                        tk.END,
                        f"[error] {message}\n\n",
                        "error",
                    )
                    self._assistant_output_text.see(tk.END)

        self.after(120, self._drain_queue)

    def _handle_output_line(self, line: str) -> None:
        self._run_log_buffer.append(line)
        verdict_hit = self.VERDICT_RE.search(line)
        if verdict_hit:
            self._current_verdict = verdict_hit.group(0)
            self.verdict_var.set(self._current_verdict)
            if self._current_verdict.startswith("PASS"):
                tag = "success"
            elif self._current_verdict.startswith("NO-EVAL"):
                tag = "warning"
            else:
                tag = "error"
            self._append_output(line, tag)
            return

        if "error" in line.lower() or "traceback" in line.lower():
            self._append_output(line, "error")
        else:
            self._append_output(line, "info")

    def _stop_running(self) -> None:
        if self._proc is None:
            self.status_var.set(_tr("No process running", "No hay proceso ejecutandose"))
            return
        try:
            self._proc.terminate()
            self._append_output("\n[terminated by user]\n", "warning")
        except Exception as e:
            self._append_output(f"\n[terminate failed] {e}\n", "error")

    def _check_local_signature(self) -> None:
        if os.name != "nt":
            messagebox.showinfo(
                "OCC Desktop",
                _tr(
                    "Authenticode check is available on Windows only.",
                    "La verificacion Authenticode solo esta disponible en Windows.",
                ),
            )
            return

        selected = filedialog.askopenfilename(
            title=_tr("Select EXE", "Seleccionar EXE"),
            filetypes=[("Executable", "*.exe"), (_tr("All", "Todos"), "*.*")],
        )
        if not selected:
            return

        exe = Path(selected).resolve()
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "Get-AuthenticodeSignature -FilePath "
                f"'{exe}' | Select-Object Status,StatusMessage,SignerCertificate "
                "| Format-List"
            ),
        ]
        self._start_command("signature-check", cmd)

    def _run_action(self, action: str) -> None:
        command = self._build_action_command(action)
        if command is None:
            return
        label, cmd = command
        self._start_command(label, cmd)

    def _build_action_command(self, action: str) -> Optional[Tuple[str, List[str]]]:
        py = sys.executable

        if action in {"judge", "module_flow"}:
            claim = self._claim()
            if claim is None:
                return None
        else:
            claim = None

        if action == "judge":
            cmd = [
                py,
                "-m",
                "occ.cli",
                "judge",
                str(claim),
                "--profile",
                self.profile_var.get().strip() or "core",
            ]
            return ("judge", cmd)

        if action == "verify":
            suite = self.suite_var.get().strip() or "extensions"
            timeout = "180" if suite == "all" else "60"
            cmd = [
                py,
                "-m",
                "occ.cli",
                "verify",
                "--suite",
                suite,
                "--strict",
                "--timeout",
                timeout,
            ]
            return ("verify", cmd)

        if action == "module_flow":
            script = self._resolve_script("mrd_flow.py")
            module_cmd = [py, str(script), str(claim), "--generate-module"]
            module_name = self.module_name_var.get().strip()
            if module_name:
                module_cmd.extend(["--module-name", module_name])
            if self.create_prediction_var.get():
                module_cmd.append("--create-prediction")
            if self.verify_generated_var.get():
                module_cmd.append("--verify-generated")
            return ("module-flow", module_cmd)

        if action == "lab_run":
            claims_dir = Path(self.lab_claims_dir_var.get().strip() or ".").resolve()
            if not claims_dir.is_dir():
                messagebox.showerror(
                    "OCC Desktop",
                    _tr(
                        f"Claims folder does not exist: {claims_dir}",
                        f"La carpeta de claims no existe: {claims_dir}",
                    ),
                )
                return None

            profiles: List[str] = []
            if self.lab_profile_core_var.get():
                profiles.append("core")
            if self.lab_profile_nuclear_var.get():
                profiles.append("nuclear")
            if not profiles:
                messagebox.showwarning(
                    "OCC Desktop",
                    _tr(
                        "Select at least one lab profile.",
                        "Selecciona al menos un perfil de lab.",
                    ),
                )
                return None

            out_dir = Path(self.lab_out_dir_var.get().strip() or "").resolve()
            if not str(out_dir).strip():
                out_dir = (
                    Path(self.workspace_var.get().strip() or ".").resolve()
                    / ".occ_lab"
                    / "latest"
                )
                self.lab_out_dir_var.set(str(out_dir))
            out_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                py,
                "-m",
                "occ.cli",
                "lab",
                "run",
                "--claims-dir",
                str(claims_dir),
                "--profiles",
                *profiles,
                "--out",
                str(out_dir),
                "--json",
            ]
            if self.lab_recursive_var.get():
                cmd.append("--recursive")
            if self.lab_strict_trace_var.get():
                cmd.append("--strict-trace")
            if self.lab_fail_on_non_pass_var.get():
                cmd.append("--fail-on-non-pass")

            return ("lab-run", cmd)

        if action == "release_doctor":
            script = self._resolve_script("release_doctor.py")
            return ("release-doctor", [py, str(script), "--strict", "--no-resolve-doi"])

        if action == "docs_i18n":
            script = self._resolve_script("check_docs_i18n.py")
            return ("docs-i18n", [py, str(script), "--strict"])

        if action == "ci_doctor":
            script = self._resolve_script("ci_doctor.py")
            return ("ci-doctor", [py, str(script), "--workflow", "CI", "--limit", "12"])

        if action == "release_notes":
            script = self._resolve_script("generate_release_notes.py")
            return ("release-notes", [py, str(script)])

        return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Launch OCC desktop application")
    parser.add_argument(
        "--headless-check",
        action="store_true",
        help="Validate module import without opening GUI",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.headless_check:
        print("ok")
        return 0

    try:
        app = OCCDesktopApp()
        app.mainloop()
        return 0
    except tk.TclError as e:
        print(
            _tr(
                "OCC Desktop requires a graphical desktop session.",
                "OCC Desktop requiere una sesion grafica de escritorio.",
            ),
            file=sys.stderr,
        )
        print(f"details: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
