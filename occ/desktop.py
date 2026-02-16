"""OCC desktop app (Windows-friendly Tkinter frontend).

This GUI wraps the existing OCC command-line workflows so users can operate the
project without terminal usage.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional, Sequence


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


class OCCDesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OCC Desktop")
        self.geometry("1120x760")
        self.minsize(980, 640)

        repo_root = Path(__file__).resolve().parents[1]
        self.repo_root = repo_root
        self.workspace_var = tk.StringVar(value=str(repo_root))
        self.claim_var = tk.StringVar(
            value=str(repo_root / "examples" / "claim_specs" / "minimal_pass.yaml")
        )
        self.profile_var = tk.StringVar(value="core")
        self.suite_var = tk.StringVar(value="extensions")
        self.module_name_var = tk.StringVar(value="")
        self.create_prediction_var = tk.BooleanVar(value=True)
        self.verify_generated_var = tk.BooleanVar(value=False)

        self.status_var = tk.StringVar(value=_tr("Ready", "Listo"))
        self._queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._proc: Optional[subprocess.Popen[str]] = None
        self._running = False
        self._buttons: List[ttk.Button] = []

        self._build_ui()
        self.after(120, self._drain_queue)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        top = ttk.LabelFrame(
            outer,
            text=_tr("Project Context", "Contexto del proyecto"),
            padding=10,
        )
        top.pack(fill=tk.X)

        ttk.Label(top, text=_tr("Workspace", "Workspace")).grid(
            row=0,
            column=0,
            sticky=tk.W,
            padx=(0, 8),
        )
        workspace_entry = ttk.Entry(top, textvariable=self.workspace_var)
        workspace_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(top, text=_tr("Browse", "Buscar"), command=self._pick_workspace).grid(
            row=0, column=2, sticky=tk.W, padx=(8, 0)
        )

        ttk.Label(top, text=_tr("Claim file", "Archivo claim")).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 8)
        )
        claim_entry = ttk.Entry(top, textvariable=self.claim_var)
        claim_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)
        ttk.Button(top, text=_tr("Browse", "Buscar"), command=self._pick_claim).grid(
            row=1, column=2, sticky=tk.W, padx=(8, 0)
        )

        ttk.Label(top, text=_tr("Judge profile", "Perfil de jueces")).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Combobox(
            top,
            textvariable=self.profile_var,
            values=["core", "nuclear"],
            state="readonly",
        ).grid(
            row=2, column=1, sticky=tk.W, pady=2
        )

        ttk.Label(top, text=_tr("Verify suite", "Suite verify")).grid(
            row=2, column=2, sticky=tk.W, padx=(8, 8)
        )
        ttk.Combobox(
            top,
            textvariable=self.suite_var,
            values=["canon", "extensions", "all"],
            state="readonly",
            width=12,
        ).grid(row=2, column=3, sticky=tk.W, pady=2)

        ttk.Label(top, text=_tr("Module name (optional)", "Nombre módulo (opcional)")).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 8)
        )
        ttk.Entry(top, textvariable=self.module_name_var).grid(
            row=3,
            column=1,
            sticky=tk.EW,
            pady=2,
        )

        ttk.Checkbutton(
            top,
            text=_tr("Create prediction draft", "Crear borrador de predicción"),
            variable=self.create_prediction_var,
        ).grid(row=3, column=2, sticky=tk.W, padx=(8, 8))
        ttk.Checkbutton(
            top,
            text=_tr(
                "Verify generated module once",
                "Verificar módulo generado una vez",
            ),
            variable=self.verify_generated_var,
        ).grid(row=3, column=3, sticky=tk.W)

        top.columnconfigure(1, weight=1)

        cmd = ttk.LabelFrame(
            outer,
            text=_tr("Actions", "Acciones"),
            padding=10,
        )
        cmd.pack(fill=tk.X, pady=(10, 0))

        self._add_button(cmd, _tr("Judge Claim", "Evaluar Claim"), self._run_judge, 0, 0)
        self._add_button(cmd, _tr("Verify Suite", "Verificar Suite"), self._run_verify, 0, 1)
        self._add_button(
            cmd,
            _tr("Module Flow", "Flujo de módulo"),
            self._run_module_flow,
            0,
            2,
        )
        self._add_button(
            cmd,
            _tr("Release Doctor", "Release Doctor"),
            self._run_release_doctor,
            1,
            0,
        )
        self._add_button(
            cmd,
            _tr("Docs i18n Audit", "Auditar docs i18n"),
            self._run_docs_i18n,
            1,
            1,
        )
        self._add_button(cmd, _tr("CI Doctor", "CI Doctor"), self._run_ci_doctor, 1, 2)
        self._add_button(
            cmd,
            _tr("Generate Release Notes", "Generar release notes"),
            self._run_release_notes,
            1,
            3,
        )
        self._add_button(cmd, _tr("Stop", "Detener"), self._stop_running, 0, 3)

        out_frame = ttk.LabelFrame(
            outer,
            text=_tr("Output", "Salida"),
            padding=8,
        )
        out_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.output = tk.Text(
            out_frame,
            wrap=tk.WORD,
            height=20,
            font=("Consolas", 10),
            background="#0f172a",
            foreground="#e2e8f0",
            insertbackground="#e2e8f0",
        )
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(out_frame, orient=tk.VERTICAL, command=self.output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=scrollbar.set)

        status = ttk.Label(outer, textvariable=self.status_var, anchor=tk.W)
        status.pack(fill=tk.X, pady=(8, 0))

    def _add_button(
        self,
        parent: ttk.LabelFrame,
        text: str,
        command: Callable[[], None],
        row: int,
        col: int,
    ) -> None:
        btn = ttk.Button(parent, text=text, command=command)
        btn.grid(row=row, column=col, sticky=tk.W, padx=(0, 8), pady=4)
        self._buttons.append(btn)

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

    def _resolve_script(self, script_name: str) -> Path:
        workspace = Path(self.workspace_var.get()).resolve()
        candidate = workspace / "scripts" / script_name
        if candidate.is_file():
            return candidate
        fallback = self.repo_root / "scripts" / script_name
        return fallback

    def _append_output(self, text: str) -> None:
        self.output.insert(tk.END, text)
        self.output.see(tk.END)

    def _set_running(self, running: bool) -> None:
        self._running = running
        for b in self._buttons:
            if b["text"] in {_tr("Stop", "Detener")}:
                continue
            b.configure(state=tk.DISABLED if running else tk.NORMAL)

    def _workspace(self) -> Optional[Path]:
        raw = self.workspace_var.get().strip()
        if not raw:
            messagebox.showerror(
                "OCC Desktop",
                _tr("Workspace is required.", "Workspace es obligatorio."),
            )
            return None
        p = Path(raw).resolve()
        if not p.is_dir():
            messagebox.showerror(
                "OCC Desktop",
                _tr("Workspace folder does not exist.", "La carpeta workspace no existe."),
            )
            return None
        return p

    def _claim(self) -> Optional[Path]:
        raw = self.claim_var.get().strip()
        if not raw:
            messagebox.showerror(
                "OCC Desktop",
                _tr("Claim file is required.", "El claim es obligatorio."),
            )
            return None
        p = Path(raw).resolve()
        if not p.is_file():
            messagebox.showerror(
                "OCC Desktop",
                _tr("Claim file does not exist.", "El archivo claim no existe."),
            )
            return None
        return p

    def _start_command(self, label: str, cmd: Sequence[str]) -> None:
        if self._running:
            messagebox.showwarning(
                "OCC Desktop",
                _tr("A command is already running.", "Ya hay un comando ejecutándose."),
            )
            return

        workspace = self._workspace()
        if workspace is None:
            return

        self._set_running(True)
        self.status_var.set(_tr(f"Running: {label}", f"Ejecutando: {label}"))
        self._append_output("\n" + "=" * 90 + "\n")
        self._append_output(f"$ {' '.join(cmd)}\n\n")

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
                    self._queue.put(("line", line))
                rc = proc.wait()
                self._queue.put(("done", str(rc)))
            except Exception as e:
                self._queue.put(("line", f"[ERROR] {e}\n"))
                self._queue.put(("done", "-1"))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_queue(self) -> None:
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if kind == "line":
                self._append_output(payload)
            elif kind == "done":
                self._proc = None
                self._set_running(False)
                rc = int(payload)
                if rc == 0:
                    self.status_var.set(_tr("Done (exit 0)", "Terminado (salida 0)"))
                else:
                    self.status_var.set(
                        _tr(f"Finished with exit {rc}", f"Terminado con salida {rc}")
                    )
                self._append_output(f"\n[exit {rc}]\n")
        self.after(120, self._drain_queue)

    def _stop_running(self) -> None:
        if self._proc is None:
            self.status_var.set(_tr("No process running", "No hay proceso ejecutándose"))
            return
        try:
            self._proc.terminate()
            self._append_output("\n[terminated by user]\n")
        except Exception as e:
            self._append_output(f"\n[terminate failed] {e}\n")

    def _run_judge(self) -> None:
        claim = self._claim()
        if claim is None:
            return
        cmd = [
            sys.executable,
            "-m",
            "occ.cli",
            "judge",
            str(claim),
            "--profile",
            self.profile_var.get().strip() or "core",
        ]
        self._start_command("judge", cmd)

    def _run_verify(self) -> None:
        suite = self.suite_var.get().strip() or "extensions"
        timeout = "180" if suite == "all" else "60"
        cmd = [
            sys.executable,
            "-m",
            "occ.cli",
            "verify",
            "--suite",
            suite,
            "--strict",
            "--timeout",
            timeout,
        ]
        self._start_command("verify", cmd)

    def _run_module_flow(self) -> None:
        claim = self._claim()
        if claim is None:
            return
        script = self._resolve_script("mrd_flow.py")
        cmd: List[str] = [
            sys.executable,
            str(script),
            str(claim),
            "--generate-module",
        ]
        module_name = self.module_name_var.get().strip()
        if module_name:
            cmd.extend(["--module-name", module_name])
        if self.create_prediction_var.get():
            cmd.append("--create-prediction")
        if self.verify_generated_var.get():
            cmd.append("--verify-generated")
        self._start_command("module-flow", cmd)

    def _run_release_doctor(self) -> None:
        script = self._resolve_script("release_doctor.py")
        cmd = [sys.executable, str(script), "--strict", "--no-resolve-doi"]
        self._start_command("release-doctor", cmd)

    def _run_docs_i18n(self) -> None:
        script = self._resolve_script("check_docs_i18n.py")
        cmd = [sys.executable, str(script), "--strict"]
        self._start_command("docs-i18n", cmd)

    def _run_ci_doctor(self) -> None:
        script = self._resolve_script("ci_doctor.py")
        cmd = [sys.executable, str(script), "--workflow", "CI", "--limit", "12"]
        self._start_command("ci-doctor", cmd)

    def _run_release_notes(self) -> None:
        script = self._resolve_script("generate_release_notes.py")
        cmd = [sys.executable, str(script)]
        self._start_command("release-notes", cmd)


def main() -> int:
    app = OCCDesktopApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
