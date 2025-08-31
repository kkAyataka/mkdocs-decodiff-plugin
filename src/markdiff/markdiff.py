import argparse
from dataclasses import dataclass, field
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class LineInfo:
    line_no: int
    col_start: int
    col_end: int
    anchor_no: int

@dataclass
class ChangeInfo:
    from_file: Optional[str] = None
    to_file: Optional[str] = None
    changed_lines: List[LineInfo] = field(default_factory=list)

def _run_git_diff(base: str, target_dir: Optional[str], unified: int = 0) -> str:
    """ Runs `git diff`. """

    args = [
        "git",
        "diff",
        "--no-color",
        "--ignore-all-space",
        "--word-diff=porcelain",
        "--unified=0",
        f"{base}",
    ]
    if target_dir:
        args.extend(["--", target_dir])

    try:
        r = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise RuntimeError("git is not available in PATH") from e

    if r.returncode > 0:
        raise RuntimeError(r.stderr.strip() or "git diff failed")
    return r.stdout

def _parse_diff(diff_text: str) -> List[ChangeInfo]:
    """ Parses a unified diff text. """

    changed: List[ChangeInfo] = []
    anchor_no = 0

    is_completed = False

    from_file = None
    to_file = None
    line_info_list: List[LineInfo] = []

    hunk_to_file_start = 0
    hunk_start = 0
    hunk_line_count = 0
    hunk_scanned_line_count = 0
    hunk_col_pos = 0

    for i, line in enumerate(diff_text.splitlines()):
        # in hunk
        if hunk_start < i and hunk_scanned_line_count < hunk_line_count:
            if line == '~':
                hunk_scanned_line_count += 1
                # hunk end
                if hunk_scanned_line_count == hunk_line_count:
                    hunk_to_file_start = 0
                    hunk_start = 0
                    hunk_line_count = 0
                    hunk_scanned_line_count = 0
                    hunk_col_pos = 0
                    #changed.append(ChangeInfo(from_file, to_file, line_info_list))
            elif line.startswith(' '):
                hunk_col_pos += len(line) - 1
            elif line.startswith('+'):
                line_info_list.append(LineInfo(
                    hunk_to_file_start + hunk_scanned_line_count,
                    hunk_col_pos,
                    hunk_col_pos + len(line) - 1,
                    anchor_no))
                anchor_no += 1
            elif line.startswith('-'):
                # ignore removed words
                pass

            continue

        # start file
        if line.startswith("diff --git "):
            if from_file is not None or to_file is not None:
                # previous file end
                changed.append(ChangeInfo(from_file, to_file, line_info_list))
            # reset
            is_completed = False
            from_file = None
            to_file = None
            line_info_list = []
            continue

        # Checks whether the current file diff parsing is completed
        if is_completed:
            continue

        # from file
        if line.startswith("---"):
            v = line[4:]
            if v.startswith("a/"):
                from_file = v[2:]
            elif v == "/dev/null":
                from_file = None
            else:
                print(f'Unexpected line {i+1}: {line}', file=sys.stderr)
            continue

        # to file
        if line.startswith("+++"):
            v = line[4:]
            if v.startswith("b/"):
                to_file = v[2:]
            elif v == "/dev/null":
                to_file = None
            else:
                print(f'Unexpected line {i+1}: {line}', file=sys.stderr)
            continue

        # checks file
        if from_file is None and to_file is None:
            continue

        # Ignore non-markdown files
        if (
            (from_file is not None and not from_file.endswith((".md", ".markdown")))
            or (to_file is not None and not to_file.endswith((".md", ".markdown")))
        ):
            is_completed = True
            continue

        # file is deleted or added
        if from_file is None or to_file is None:
            is_completed = True
            changed.append(ChangeInfo(from_file, to_file, []))
            continue

        # hunk
        if line.startswith("@@ "):
            # @@ -old_start,old_count +new_start,new_count @@
            m = re.match(r"@@ -\d+(?:,(?P<fc>\d+))? \+(?P<ts>\d+)(?:,(?P<tc>\d+))? @@", line)
            if not m:
                print(f'Unexpected line {i+1}: {line}', file=sys.stderr)
                continue
            from_count = int(m.group('fc') or '1')
            to_start = int(m.group('ts'))
            to_count = int(m.group('tc') or '1')

            hunk_to_file_start = to_start
            hunk_start = i
            hunk_line_count = max(from_count, to_count)
            continue

    if from_file is not None or to_file is not None:
        # previous file end
        changed.append(ChangeInfo(from_file, to_file, line_info_list))
    # remove empty entries
    return changed

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

        wrapped = f"{prefix}<span id=\"{anchor_id}\" class=\"{cls}\">{body}</span>"
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
    unified: int = 0,
) -> int:
    diff = _run_git_diff(base, target_dir, unified)
    changes = _parse_diff(diff)

    for c in changes:
        if c.from_file is None or c.to_file is None:
            continue

        if c.changed_lines is None or len(c.changed_lines) == 0:
            continue

        new_lines = []
        changed_line_iterator = iter(c.changed_lines)
        next_changed_line = next(changed_line_iterator, None)
        is_code_block = False
        is_table = False
        with open(c.to_file, "r", newline='', encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if next_changed_line is None:
                    new_lines.append(line)
                    continue

                # checks code block
                if re.search(r'^\s*```', line):
                    is_code_block = False if is_code_block else True
                    is_table = False

                # checks table
                if re.search(r'^(|)?[\s-:]*\|[\s-:]*', line):
                    is_table = True

                if re.search(r'^[\r\n]+$', line):
                    is_table = False

                if i == next_changed_line.line_no:
                    if (
                        is_code_block
                        or re.search(r'^\s*[*=-]+$', line)
                    ):
                        new_lines.append(line)
                        next_changed_line = next(changed_line_iterator, None)
                        continue

                    offset = 0
                    if next_changed_line.col_start == 0:
                        if m := re.search(r'^#+ ', line):
                            offset = m.end()
                        elif m := re.search(r'^\s*[*\-+] (\[[ xX]\] )?', line):
                            offset = m.end()
                        elif m := re.search(r'^\s*\d+[.)] ', line):
                            offset = m.end()
                        elif m := re.search(r'^> ', line):
                            offset = m.end()

                    start = next_changed_line.col_start + offset
                    end = next_changed_line.col_end
                    anchor_no = next_changed_line.anchor_no
                    new_line = line[:start] \
                        + f'<span id="markdiff-anchor-{anchor_no}" class="markdiff-diff">' \
                        + line[start:end] + '</span>' + line[end:]
                    new_lines.append(new_line)

                    print(f'--- anchor {next_changed_line.anchor_no} ---')
                    print(line)
                    print(new_line)
                    next_changed_line = next(changed_line_iterator, None)
                else:
                    new_lines.append(line)

        with open(c.to_file, "w", newline='', encoding="utf-8") as f:
            f.writelines(new_lines)

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
            lines = _read_text(fs_path)
        except UnicodeDecodeError:
            continue
        new_lines, anchors = _annotate_lines(lines, changed_lines)
        _write_text(fs_path, new_lines)
        for _line_no, anchor_id, label in anchors:
            grouped_links.setdefault(file_path, []).append((anchor_id, label))

    if change_list_file and grouped_links:
        # Produce a Markdown change list grouped by file with metadata
        from datetime import date
        lines: List[str] = ["# Changes\n\n"]
        lines.append(f"* Generated on: {date.today().isoformat()}\n")
        lines.append(f"* Base commit: {base}\n\n")

        for file_path, anchors in grouped_links.items():
            lines.append(f"## [{file_path}]({file_path})\n\n")
            for anchor_id, label in anchors:
                # Fallback label if empty
                link_label = label if label.strip() else anchor_id
                link = f"{file_path}#{anchor_id}"
                lines.append(f"* [{link_label}]({link})\n")
            lines.append("\n")
        os.makedirs(os.path.dirname(change_list_file) or ".", exist_ok=True)
        _write_text(change_list_file, lines)

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
        "--unified",
        type=int,
        default=0,
        help="Lines of context for git diff (passed to --unified=N)",
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
        return run(args.base, args.target_dir, args.change_list_file, args.unified)
    except Exception as e:
        print(f"markdiff error: {e}")
        return 2
