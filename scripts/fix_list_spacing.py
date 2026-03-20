#!/usr/bin/env python3
"""
fix_list_spacing.py
-------------------
Ensures a blank line exists before every ordered/unordered list item that
immediately follows a non-blank, non-list, non-header, non-fence line.

Without the blank line, Python-Markdown (used by MkDocs) swallows list items
into the preceding paragraph, rendering them inline as plain text.

Usage:
    python3 scripts/fix_list_spacing.py [--check]

    --check   Report issues without modifying files (exit 1 if any found).
              Omit to apply fixes in-place.
"""

import argparse
import glob
import os
import re
import sys

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
LIST_START = re.compile(r"^\s*(\d+[.)]\s|\*\s|-\s|•\s)")


def is_fence(line: str) -> bool:
    s = line.lstrip()
    return s.startswith("```") or s.startswith("~~~")


def process_file(path: str, check_only: bool) -> int:
    """Return number of issues found (and fixed if not check_only)."""
    with open(path) as f:
        lines = f.readlines()

    result = []
    in_code = False
    issues = 0

    for line in lines:
        if is_fence(line):
            in_code = not in_code

        if not in_code and LIST_START.match(line):
            prev = result[-1].rstrip() if result else ""
            prev_l = prev.lstrip()
            if (
                prev
                and not LIST_START.match(prev)
                and not prev_l.startswith("#")
                and not is_fence(prev)
                and not prev_l.startswith("---")
                and not prev_l.startswith(">")
            ):
                issues += 1
                if not check_only:
                    result.append("\n")

        result.append(line)

    if issues and not check_only:
        with open(path, "w") as f:
            f.writelines(result)

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report issues without modifying files (exits 1 if any found).",
    )
    args = parser.parse_args()

    docs_dir = os.path.abspath(DOCS_DIR)
    md_files = sorted(glob.glob(os.path.join(docs_dir, "**", "*.md"), recursive=True))

    total = 0
    for path in md_files:
        rel = os.path.relpath(path, docs_dir)
        count = process_file(path, check_only=args.check)
        if count:
            action = "found" if args.check else "fixed"
            print(f"{rel}: {action} {count} missing blank line(s) before list(s)")
            total += count

    if total == 0:
        print("All good — no missing blank lines before lists.")
    elif args.check:
        print(f"\n{total} issue(s) found. Run without --check to fix.")
        sys.exit(1)
    else:
        print(f"\n{total} blank line(s) inserted across {len(md_files)} file(s) scanned.")


if __name__ == "__main__":
    main()
