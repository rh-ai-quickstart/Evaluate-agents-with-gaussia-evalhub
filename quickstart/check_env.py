from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "quickstart"))

from common import load_env_files  # noqa: E402

SHOW_VARS = (
    "EVALHUB_BASE_URL",
    "EVALHUB_TENANT",
    "EVALHUB_INSECURE",
    "MLFLOW_TRACKING_URI",
    "GAUSSIA_JUDGE_MODEL",
    "GAUSSIA_JUDGE_BASE_URL",
    "GAUSSIA_JUDGE_MODEL_PROVIDER",
    "GAUSSIA_GUARDIAN_MODEL",
    "GAUSSIA_GUARDIAN_BASE_URL",
    "GAUSSIA_GUARDIAN_TOKENIZER_MODEL",
    "GAUSSIA_GUARDIAN_CHAT_COMPLETIONS",
    "GAUSSIA_AGENTIC_K",
    "GAUSSIA_PROVIDER_PACKAGE_SPEC",
)

PROVIDER_VARS = (
    "GAUSSIA_JUDGE_MODEL",
    "GAUSSIA_JUDGE_BASE_URL",
    "GAUSSIA_JUDGE_API_KEY",
    "GAUSSIA_GUARDIAN_MODEL",
    "GAUSSIA_GUARDIAN_TOKENIZER_MODEL",
    "GAUSSIA_GUARDIAN_BASE_URL",
    "GAUSSIA_GUARDIAN_API_KEY",
    "GAUSSIA_GUARDIAN_CHAT_COMPLETIONS",
    "GAUSSIA_AGENTIC_K",
    "GAUSSIA_AGENTIC_THRESHOLD",
    "GAUSSIA_AGENTIC_TOOL_THRESHOLD",
)

EXTERNAL_VARS = (
    "EVALHUB_BASE_URL",
    "EVALHUB_AUTH_TOKEN",
    "EVALHUB_TENANT",
)

SECRET_MARKERS = ("API_KEY", "AUTH_TOKEN", "TRACKING_TOKEN")


def load_env() -> None:
    load_env_files(REPO_ROOT / ".env", REPO_ROOT / "quickstart" / ".env")


def is_secret(name: str) -> bool:
    return any(marker in name for marker in SECRET_MARKERS)


def is_placeholder(value: str) -> bool:
    return not value or value.startswith("<") or "example.com" in value


def show() -> None:
    load_env()
    print("Variables loaded from .env:")
    for name in SHOW_VARS:
        value = os.environ.get(name, "")
        if is_secret(name):
            if value:
                print(f"  {name}=(set, {len(value)} chars)")
            else:
                print(f"  {name}=(unset)")
            continue
        if not value:
            print(f"  {name}=(unset)")
        elif value.startswith("<"):
            print(f"  {name}=(placeholder)")
        else:
            print(f"  {name}={value}")


def verify(names: tuple[str, ...], profile: str) -> int:
    load_env()
    missing = [name for name in names if is_placeholder(os.environ.get(name, ""))]
    if missing:
        for name in missing:
            print(f"Error: {name} is unset or still a placeholder in .env", file=sys.stderr)
        print(f"Fix .env and rerun: make env-show", file=sys.stderr)
        return 1
    if profile == "judge/guardian":
        provider = os.environ.get("GAUSSIA_JUDGE_MODEL_PROVIDER", "openai").strip().lower()
        package_spec = os.environ.get(
            "GAUSSIA_PROVIDER_PACKAGE_SPEC",
            "gaussia[evalhub]==1.1.0b2 langchain-openai",
        )
        required = {
            "litellm": "langchain-litellm",
            "openai": "langchain-openai",
        }.get(provider)
        if required and required not in package_spec:
            print(
                f"Error: GAUSSIA_JUDGE_MODEL_PROVIDER={provider} requires "
                f"{required} in GAUSSIA_PROVIDER_PACKAGE_SPEC",
                file=sys.stderr,
            )
            return 1
    print(f".env {profile} variables are set.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or verify quickstart .env loading.")
    parser.add_argument(
        "command",
        choices=("show", "verify-provider", "verify-external"),
        help="show loaded values or verify a variable profile",
    )
    args = parser.parse_args()

    if args.command == "show":
        show()
        return 0
    if args.command == "verify-provider":
        return verify(PROVIDER_VARS, "judge/guardian")
    return verify(EXTERNAL_VARS, "external EvalHub")


if __name__ == "__main__":
    raise SystemExit(main())
