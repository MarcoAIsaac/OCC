#!/usr/bin/env python3
"""Summarize recent GitHub Actions failures using gh CLI."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass
class RunFinding:
    run_id: int
    workflow: str
    title: str
    branch: str
    status: str
    conclusion: str
    url: str
    failing_jobs: List[str]


def _run_gh(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )


def _require_gh() -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI is not installed. Install from https://cli.github.com/")

    auth = _run_gh(["auth", "status"])
    if auth.returncode != 0:
        raise RuntimeError("gh is not authenticated. Run: gh auth login")


def _json_or_empty(proc: subprocess.CompletedProcess[str]) -> Any:
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except Exception:
        return None


def collect_findings(limit: int, workflow: str | None) -> List[RunFinding]:
    _require_gh()

    fields = "databaseId,name,workflowName,displayTitle,headBranch,status,conclusion,url"
    cmd = ["run", "list", "--limit", str(max(1, limit)), "--json", fields]
    if workflow:
        cmd.extend(["--workflow", workflow])
    proc = _run_gh(cmd)
    raw = _json_or_empty(proc)
    if not isinstance(raw, list):
        raise RuntimeError(f"Could not read run list: {proc.stderr.strip() or proc.stdout.strip()}")

    bad = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}

    failures: List[RunFinding] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        conclusion = str(item.get("conclusion") or "")
        if conclusion not in bad:
            continue

        run_id = int(item.get("databaseId") or 0)
        view = _run_gh(["run", "view", str(run_id), "--json", "jobs"])
        details = _json_or_empty(view)

        jobs: List[str] = []
        if isinstance(details, dict):
            raw_jobs = details.get("jobs")
            if isinstance(raw_jobs, list):
                for job in raw_jobs:
                    if not isinstance(job, dict):
                        continue
                    jc = str(job.get("conclusion") or "")
                    if jc in bad:
                        jobs.append(str(job.get("name") or "unknown-job"))

        failures.append(
            RunFinding(
                run_id=run_id,
                workflow=str(item.get("workflowName") or item.get("name") or ""),
                title=str(item.get("displayTitle") or ""),
                branch=str(item.get("headBranch") or ""),
                status=str(item.get("status") or ""),
                conclusion=conclusion,
                url=str(item.get("url") or ""),
                failing_jobs=jobs,
            )
        )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize recent failing GitHub Actions runs.")
    parser.add_argument("--limit", type=int, default=12, help="How many recent runs to inspect")
    parser.add_argument("--workflow", help="Workflow name filter (e.g., CI)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return non-zero when failures are found",
    )
    args = parser.parse_args()

    try:
        findings = collect_findings(limit=args.limit, workflow=args.workflow)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 2

    if args.json:
        print(
            json.dumps(
                {
                    "schema": "occ.ci_doctor.v1",
                    "count": len(findings),
                    "findings": [
                        {
                            "run_id": f.run_id,
                            "workflow": f.workflow,
                            "title": f.title,
                            "branch": f.branch,
                            "status": f.status,
                            "conclusion": f.conclusion,
                            "url": f.url,
                            "failing_jobs": f.failing_jobs,
                        }
                        for f in findings
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        if not findings:
            print("No failing runs found in the selected window.")
        for f in findings:
            print(f"- [{f.workflow}] run {f.run_id} ({f.conclusion}) on {f.branch}")
            if f.title:
                print(f"  title: {f.title}")
            if f.failing_jobs:
                print(f"  failing jobs: {', '.join(f.failing_jobs)}")
            if f.url:
                print(f"  url: {f.url}")

        if findings:
            print("\nSuggested next step:")
            print("  gh run view <RUN_ID> --log-failed")

    if args.fail_on_findings and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
