from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time


def run_oc(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["oc", *args], capture_output=True, text=True, check=check)


def wait_submit_job(namespace: str, run_name: str, timeout_seconds: int) -> None:
    job_name = f"{run_name}-submit"
    print(f"Waiting for submit job {job_name} ...")
    result = run_oc(
        "wait",
        "--for=condition=complete",
        f"job/{job_name}",
        "-n",
        namespace,
        f"--timeout={timeout_seconds}s",
        check=False,
    )
    if result.returncode != 0:
        failed = run_oc(
            "wait",
            "--for=condition=failed",
            f"job/{job_name}",
            "-n",
            namespace,
            "--timeout=5s",
            check=False,
        )
        logs = run_oc("logs", f"job/{job_name}", "-n", namespace, check=False)
        if failed.returncode == 0:
            print(logs.stdout, file=sys.stderr)
            if logs.stderr:
                print(logs.stderr, file=sys.stderr)
            raise SystemExit(f"Submit job {job_name} failed.")
        raise SystemExit(result.stderr.strip() or f"Timed out waiting for submit job {job_name}.")


def parse_submit_payload(logs: str) -> dict:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", logs):
        try:
            payload, _ = decoder.raw_decode(logs, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("job_id"):
            return payload
    raise SystemExit("Could not parse job_id from submit job logs.")


def job_state(item: dict) -> str:
    status = item.get("status", {})
    if status.get("succeeded", 0) >= 1:
        return "complete"
    for condition in status.get("conditions", []):
        if condition.get("type") == "Failed" and condition.get("status") == "True":
            return "failed"
    return "active"


def job_counts(namespace: str, job_id: str) -> tuple[int, int, int]:
    result = run_oc(
        "get",
        "jobs",
        "-l",
        f"job_id={job_id}",
        "-n",
        namespace,
        "-o",
        "json",
    )
    items = json.loads(result.stdout).get("items", [])
    active = complete = failed = 0
    for item in items:
        state = job_state(item)
        if state == "failed":
            failed += 1
        elif state == "complete":
            complete += 1
        else:
            active += 1
    return len(items), complete, failed


def wait_benchmark_jobs(
    namespace: str,
    job_id: str,
    expected_count: int,
    timeout_seconds: int,
    poll_seconds: int,
) -> None:
    print(f"Waiting for {expected_count} EvalHub benchmark jobs (job_id={job_id}) ...")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        total, complete, failed = job_counts(namespace, job_id)
        if failed:
            failed_jobs = run_oc(
                "get",
                "jobs",
                "-l",
                f"job_id={job_id}",
                "-n",
                namespace,
                "-o",
                "json",
            )
            for item in json.loads(failed_jobs.stdout).get("items", []):
                if job_state(item) != "failed":
                    continue
                name = item["metadata"]["name"]
                logs = run_oc("logs", f"job/{name}", "-n", namespace, check=False)
                print(f"\n--- logs for failed job {name} ---", file=sys.stderr)
                print(logs.stdout[-8000:], file=sys.stderr)
                if logs.stderr:
                    print(logs.stderr, file=sys.stderr)
            raise SystemExit(f"{failed} benchmark job(s) failed for job_id={job_id}.")
        if total >= expected_count and complete == total:
            print(f"All {complete} benchmark jobs completed successfully.")
            return
        print(
            f"  progress: {complete}/{expected_count} complete, "
            f"{total - complete - failed} active, {failed} failed"
        )
        time.sleep(poll_seconds)
    raise SystemExit(
        f"Timed out after {timeout_seconds}s waiting for benchmark jobs (job_id={job_id})."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for a quickstart run to finish.")
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--submit-timeout", type=int, default=600)
    parser.add_argument("--benchmark-timeout", type=int, default=3600)
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()

    wait_submit_job(args.namespace, args.run_name, args.submit_timeout)
    logs = run_oc("logs", f"job/{args.run_name}-submit", "-n", args.namespace)
    payload = parse_submit_payload(logs.stdout)
    benchmark_ids = payload.get("benchmark_ids") or []
    if not benchmark_ids:
        raise SystemExit("Submit job did not report benchmark_ids.")
    wait_benchmark_jobs(
        args.namespace,
        payload["job_id"],
        len(benchmark_ids),
        args.benchmark_timeout,
        args.poll_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
