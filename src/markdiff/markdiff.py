import argparse
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from ._git_diff import WordDiff, parse_porcelain_diff, run_git_diff
from .markdown_marker import mark_markdown

_HEAD_RE = re.compile(r"^(?P<prefix>\s*#{1,6}\s+)(?P<body>.*)$")
_TASK_RE = re.compile(r"^(?P<prefix>\s*[-*+]\s+\[[ xX]\]\s+)(?P<body>.*)$")
_UL_RE = re.compile(r"^(?P<prefix>\s*[-*+]\s+)(?P<body>.*)$")
_OL_RE = re.compile(r"^(?P<prefix>\s*\d+\.\s+)(?P<body>.*)$")
_BQ_RE = re.compile(r"^(?P<prefix>\s*>\s+)(?P<body>.*)$")


def _split_leading_markup(text: str) -> Tuple[str, str]:
    for rx in (_HEAD_RE, _TASK_RE, _UL_RE, _OL_RE, _BQ_RE):
        m = rx.match(text)
        if m:
            return m.group("prefix"), m.group("body")
    return "", text


def _annotate_lines(
    content: List[str],
    changed_lines: Set[int],
    id_prefix: str = "markdiff-hunk-",
    cls: str = "markdiff-diff",
) -> Tuple[List[str], List[Tuple[int, str, str]]]:
    anchors: List[Tuple[int, str, str]] = []
    counter = 1
    out: List[str] = []
    for idx, line in enumerate(content, start=1):
        if idx not in changed_lines:
            out.append(line)
            continue
        # Keep line ending
        if line.endswith("\n"):
            raw = line[:-1]
            end = "\n"
        else:
            raw = line
            end = ""

        prefix, body = _split_leading_markup(raw)

        anchor_id = f"{id_prefix}{counter}"
        counter += 1

        wrapped = f'{prefix}<span id="{anchor_id}" class="{cls}">{body}</span>'
        out.append(wrapped + end)
        anchors.append((idx, anchor_id, body))
    return out, anchors


def _write_text(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _read_text(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def run(
    base: str,
    target_dir: Optional[str],
    change_list_file: Optional[str],
) -> int:
    diff = run_git_diff(base, WordDiff.PORCELAIN, target_dir)
    changes = parse_porcelain_diff(diff)

    for c in changes:
        if c.from_file is None or c.to_file is None:
            continue

        if c.changed_lines is None or len(c.changed_lines) == 0:
            continue

        md_lines = mark_markdown(c.to_file)

        changed_line_iter = iter(c.changed_lines)
        changed_line = next(changed_line_iter, None)
        new_lines = []
        for i, md_line in enumerate(md_lines, start=1):
            if changed_line is None:
                new_lines.append(md_line.line)
                continue

            if i == changed_line.line_no:
                if md_line.is_code_block() or md_line.is_h_rule() or md_line.is_table():
                    new_lines.append(md_line.line)
                    changed_line = next(changed_line_iter, None)
                    continue

                offset = 0
                if changed_line.col_start == 0:
                    if m := re.search(r"^#+ ", md_line.line):
                        offset = m.end()
                    elif m := re.search(r"^\s*[*\-+] (\[[ xX]\] )?", md_line.line):
                        offset = m.end()
                    elif m := re.search(r"^\s*\d+[.)] ", md_line.line):
                        offset = m.end()
                    elif m := re.search(r"^> ", md_line.line):
                        offset = m.end()

                start = changed_line.col_start + offset
                end = changed_line.col_end
                anchor_no = changed_line.anchor_no
                new_line = (
                    md_line.line[:start]
                    + f'<span id="markdiff-anchor-{anchor_no}" class="markdiff-diff">'
                    + md_line.line[start:end]
                    + "</span>"
                    + md_line.line[end:]
                )
                new_lines.append(new_line)

                print(f"--- anchor {changed_line.anchor_no} ---")
                print(md_line.line)
                print(new_line)
                changed_line = next(changed_line_iter, None)
            else:
                new_lines.append(md_line.line)

        # with open(c.to_file, "w", newline="", encoding="utf-8") as f:
        #     f.writelines(new_lines)

    return 0
    # file -> list of (anchor_id, label)
    grouped_links: Dict[str, List[Tuple[str, str]]] = {}

    for file_path, changed_lines in changed_map.items():
        # Resolve on-disk path from repo root; git paths are relative
        fs_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(fs_path):
            # skip missing files (renames/deletes etc.)
            continue
        try:
            md_lines = _read_text(fs_path)
        except UnicodeDecodeError:
            continue
        new_lines, anchors = _annotate_lines(md_lines, changed_lines)
        _write_text(fs_path, new_lines)
        for _line_no, anchor_id, label in anchors:
            grouped_links.setdefault(file_path, []).append((anchor_id, label))

    if change_list_file and grouped_links:
        # Produce a Markdown change list grouped by file with metadata
        from datetime import date

        md_lines: List[str] = ["# Changes\n\n"]
        md_lines.append(f"* Generated on: {date.today().isoformat()}\n")
        md_lines.append(f"* Base commit: {base}\n\n")

        for file_path, anchors in grouped_links.items():
            md_lines.append(f"## [{file_path}]({file_path})\n\n")
            for anchor_id, label in anchors:
                # Fallback label if empty
                link_label = label if label.strip() else anchor_id
                link = f"{file_path}#{anchor_id}"
                md_lines.append(f"* [{link_label}]({link})\n")
            md_lines.append("\n")
        os.makedirs(os.path.dirname(change_list_file) or ".", exist_ok=True)
        _write_text(change_list_file, md_lines)

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="markdiff",
        description=(
            "Insert HTML tags into Markdown files for changed lines based on git diff."
        ),
    )
    p.add_argument(
        "--base",
        required=True,
        help="Base commit, tag, or branch to diff against (compares base..HEAD)",
    )
    p.add_argument(
        "--dir",
        dest="target_dir",
        default=None,
        help="Target directory to limit diff (e.g., docs)",
    )
    p.add_argument(
        "--change-list-file",
        dest="change_list_file",
        default=None,
        help="Path to write a Markdown list of links to changed anchors",
    )
    p.add_argument(
        "--min-change-chars",
        type=int,
        default=3,
        help="Minimum changed characters; shorter changes aren’t annotated or listed.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        return run(args.base, args.target_dir, args.change_list_file)
    except Exception as e:
        print(f"markdiff error: {e}")
        return 2
