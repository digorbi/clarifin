"""Validate a generated bank statement parser for code quality and correctness.

Usage:
    python check_parser.py <parser_file_or_output_dir> --check ruff|mypy|self-test|structure
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_parser(path: Path) -> Path | None:
    if path.is_file():
        return path
    candidates = sorted(path.rglob("extract_*.py"))
    return candidates[0] if candidates else None


def check_ruff(p: Path) -> tuple[bool, str]:
    r = subprocess.run(["ruff", "check", str(p)], capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip() or "no issues"


def check_mypy(p: Path) -> tuple[bool, str]:
    r = subprocess.run(["mypy", "--strict", str(p)], capture_output=True, text=True)
    return r.returncode == 0, r.stdout.strip() or "no issues"


def check_self_test(p: Path) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(p), "--self-test"],
        capture_output=True,
        text=True,
        cwd=p.parent.parent,
    )
    output = r.stdout.strip() or r.stderr.strip()
    return r.returncode == 0, output


def check_structure(p: Path) -> tuple[bool, str]:
    code = p.read_text()
    required = ["parse_pdf", "Transaction", "Statement", "_self_test", "ValueError"]
    missing = [s for s in required if s not in code]
    if missing:
        return False, f"missing required symbols: {missing}"
    return True, "all required symbols present"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="parser file or eval output directory")
    ap.add_argument(
        "--check",
        required=True,
        choices=["ruff", "mypy", "self-test", "structure"],
    )
    args = ap.parse_args()

    parser_path = find_parser(Path(args.target))
    if parser_path is None:
        print(f"FAIL: no extract_*.py found in {args.target}")
        sys.exit(1)

    checks = {
        "ruff": check_ruff,
        "mypy": check_mypy,
        "self-test": check_self_test,
        "structure": check_structure,
    }
    passed, evidence = checks[args.check](parser_path)
    print(f"{'PASS' if passed else 'FAIL'} [{args.check}] {parser_path.name}: {evidence}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
