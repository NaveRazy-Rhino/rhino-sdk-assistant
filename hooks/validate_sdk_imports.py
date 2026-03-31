#!/usr/bin/env python3
"""PostToolUse hook: validates rhino-health SDK import paths after Write/Edit."""

import json
import re
import sys
from pathlib import Path

BAD_PATTERNS = [
    (
        re.compile(r"from\s+rhino_health\.metrics\b"),
        "Wrong import: 'from rhino_health.metrics' should be 'from rhino_health.lib.metrics'",
    ),
    (
        re.compile(r"from\s+rhino_health\.endpoints\b"),
        "Wrong import: 'from rhino_health.endpoints' should be 'from rhino_health.lib.endpoints'",
    ),
    (
        re.compile(
            r"""(?:rh|rhino_health)\.login\([^)]*password\s*=\s*["'][^"']+["']"""
        ),
        "Security: plaintext password in login() call — use password=getpass() instead",
    ),
]


def _extract_file_path(hook_input: dict) -> str:
    candidates = [
        hook_input.get("file_path"),
        hook_input.get("path"),
        hook_input.get("filePath"),
    ]
    tool_input = hook_input.get("tool_input", {})
    candidates.extend(
        [
            tool_input.get("file_path"),
            tool_input.get("path"),
            tool_input.get("filePath"),
        ]
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return ""


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return

    file_path = _extract_file_path(hook_input)

    if not file_path.endswith(".py"):
        print("{}")
        return

    if Path(file_path).name == "validate_sdk_imports.py":
        print("{}")
        return

    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print("{}")
        return

    if "rhino_health" not in content:
        print("{}")
        return

    warnings = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        for pattern, message in BAD_PATTERNS:
            if pattern.search(line):
                warnings.append(f"  Line {lineno}: {message}")

    if not warnings:
        print("{}")
        return

    detail = "\n".join(warnings)
    result = {
        "systemMessage": f"SDK Import Validation found issues:\n{detail}",
        "continue": True,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
