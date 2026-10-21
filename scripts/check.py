"""Run every quality gate in order. Same checks the pre-commit hooks and Definition of Done use."""

import subprocess
import sys

PY = sys.executable
LINT_IMPORTS = "import sys; from importlinter.cli import lint_imports_command as c; sys.exit(c())"

STEPS: list[tuple[str, list[str]]] = [
    ("ruff lint", [PY, "-m", "ruff", "check", "."]),
    ("ruff format", [PY, "-m", "ruff", "format", "--check", "."]),
    ("mypy --strict", [PY, "-m", "mypy"]),
    ("import-linter (architecture)", [PY, "-c", LINT_IMPORTS]),
    ("pytest", [PY, "-m", "pytest", "-q"]),
]


def main() -> int:
    failed: list[str] = []
    for label, command in STEPS:
        sys.stdout.write(f"\n=== {label} ===\n")
        sys.stdout.flush()
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            failed.append(label)
    if failed:
        sys.stdout.write(f"\nFAILED: {', '.join(failed)}\n")
        return 1
    sys.stdout.write("\nAll checks passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
