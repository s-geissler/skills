#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Sequence


DEFAULT_ASK_INSTRUCTIONS = (
    "You are a precise code analyst. Answer only from the supplied "
    "files. Cite file paths when making claims. If the answer is not "
    "in the supplied files, say so."
)

DEFAULT_WRITE_INSTRUCTIONS = (
    "You generate boilerplate for coding projects. Return only the "
    "complete target file contents, with no markdown fences, no "
    "preamble, and no explanation."
)

DEFAULT_REVIEW_INSTRUCTIONS = """\
You are a strict code reviewer. Compare the provided code changes against \
the requirements document. For each requirement, state whether it is \
satisfied by the changes. List any deviations, missing implementations, \
or violations. Conclude with a final verdict line exactly matching either \
"VERDICT: PASS" or "VERDICT: FAIL". Provide concise streaming updates during the review process.
"""


def run_opencode(
    *,
    model: str | None,
    agent: str | None,
    files: Sequence[str | pathlib.Path],
    message: str,
) -> str:
    cmd = ["opencode", "run", "--dangerously-skip-permissions", "--format", "json"]
    if model:
        cmd.extend(["-m", model])
    if agent:
        cmd.extend(["--agent", agent])
    for f in files:
        cmd.extend(["-f", str(f)])
    cmd.append("--")
    cmd.append(message)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    return extract_text(result.stdout)


def extract_text(stdout: str) -> str:
    texts = []
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            part = event.get("part", {})
            text = part.get("text", "")
            if text:
                texts.append(text)
    return "".join(texts)


def cmd_ask(args: argparse.Namespace) -> int:
    prompt = f"{DEFAULT_ASK_INSTRUCTIONS}\n\nQuestion: {args.question}"
    output = run_opencode(
        model=args.model, agent=args.agent, files=args.paths, message=prompt
    )
    print(output)
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    target = pathlib.Path(args.target)
    if target.exists() and not args.overwrite:
        print(
            f"{target} already exists. Pass --overwrite to replace it.",
            file=sys.stderr,
        )
        return 1

    prompt = (
        f"{DEFAULT_WRITE_INSTRUCTIONS}\n\n"
        f"Target path: {target}\n"
        f"Spec:\n{args.spec}\n\n"
        "Write the complete file contents now."
    )
    content = run_opencode(
        model=args.model, agent=args.agent, files=args.context, message=prompt
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(target)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    against_path = pathlib.Path(args.against)
    if not against_path.exists():
        print(f"Reference document not found: {against_path}", file=sys.stderr)
        return 1

    diff_content = None
    review_files = list(args.paths) if args.paths else []

    if args.diff:
        diff_path = pathlib.Path(args.diff)
        if not diff_path.exists():
            print(f"Diff file not found: {diff_path}", file=sys.stderr)
            return 1
        diff_content = diff_path.read_text(encoding="utf-8")
    elif not review_files:
        git_cmd = ["git", "diff", "--staged"] if args.staged else ["git", "diff", "HEAD"]
        result = subprocess.run(git_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return 1
        diff_content = result.stdout
        if not diff_content.strip():
            print("No changes to review.", file=sys.stderr)
            return 0

    prompt_parts = [DEFAULT_REVIEW_INSTRUCTIONS]

    if diff_content:
        prompt_parts.append(f"\n\n## Code Changes (diff)\n\n```diff\n{diff_content}\n```")

    if review_files:
        prompt_parts.append(
            f"\n\n## Additional Files to Review\n\n{', '.join(str(f) for f in review_files)}"
        )

    prompt_parts.append(
        "\n\nReview the code changes against the requirements document. Provide your analysis."
    )
    prompt = "\n".join(prompt_parts)

    files = [against_path] + review_files
    output = run_opencode(
        model=args.model, agent=args.agent, files=files, message=prompt
    )
    print(output)

    for line in output.splitlines():
        if line.strip() == "VERDICT: FAIL":
            return 1
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="delegate",
        description=(
            "Dispatch LLM queries via the opencode CLI. "
            "It is encouraged to configure an opencode agent with appropriate tool permissions."
        ),
    )
    parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="Model to use (provider/model). Defaults to opencode's configured default.",
    )
    parser.add_argument(
        "-a",
        "--agent",
        default=None,
        help="Agent to use for the query.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Ask a question about files.")
    ask_parser.add_argument("--paths", nargs="+", required=True, help="Files to read.")
    ask_parser.add_argument("--question", required=True, help="Question to answer.")

    write_parser = subparsers.add_parser("write", help="Generate a file from a spec.")
    write_parser.add_argument("--spec", required=True, help="What to generate.")
    write_parser.add_argument(
        "--context",
        nargs="*",
        default=[],
        help="Reference files to include as context.",
    )
    write_parser.add_argument("--target", required=True, help="Output file path.")
    write_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace target if it already exists.",
    )

    review_parser = subparsers.add_parser(
        "review", help="Review code changes against a requirements document."
    )
    review_parser.add_argument(
        "--against", required=True, help="Path to the issue/PRD document to review against."
    )
    review_group = review_parser.add_mutually_exclusive_group()
    review_group.add_argument(
        "--diff", default=None, help="Path to a diff file to review."
    )
    review_group.add_argument(
        "--paths", nargs="+", default=[], help="Explicit file paths to review."
    )
    review_parser.add_argument(
        "--staged",
        action="store_true",
        help="Use staged git diff instead of all changes since HEAD.",
    )

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "ask":
        return cmd_ask(args)
    elif args.command == "write":
        return cmd_write(args)
    elif args.command == "review":
        return cmd_review(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
