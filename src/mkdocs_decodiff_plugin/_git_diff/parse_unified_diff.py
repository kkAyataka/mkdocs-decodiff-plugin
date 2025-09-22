import re
import sys
from typing import List

from .git_diff import FileDiff, LineDiff


def parse_unified_diff(diff_text: str) -> List[FileDiff]:
    """Parses unified diff (git diff --word-diff=none) text"""

    diffs: List[FileDiff] = []
    diff_lines: List[LineDiff] = []
    is_not_markdown = False
    is_removed_or_added_file = False
    from_file = None
    to_file = None
    anchor_no = 0
    hunk_to_file_start = 0
    hunk_start_index = 0
    hunk_end_index = 0
    hunk_scanned_line_count = 0
    for i, line in enumerate(diff_text.splitlines()):
        # in hunk
        if hunk_start_index < i and i <= hunk_end_index:
            if is_removed_or_added_file:
                # ignore
                pass
            elif line.startswith("-"):
                # ignore removed lines
                pass
            elif line.startswith("+"):
                diff_lines.append(
                    LineDiff(
                        hunk_to_file_start + hunk_scanned_line_count,
                        0,
                        len(line) - 1,
                        anchor_no,
                    )
                )
                hunk_scanned_line_count += 1
                anchor_no += 1

            # hunk is end
            if i == hunk_end_index:
                hunk_to_file_start = 0
                hunk_start_index = 0
                hunk_end_index = 0
                hunk_scanned_line_count = 0
            continue

        # start file
        if line.startswith("diff --git "):
            if not is_not_markdown and (from_file is not None or to_file is not None):
                # save previouse file
                diffs.append(FileDiff(from_file, to_file, diff_lines))

            # reset
            diff_lines = []
            is_not_markdown = False
            is_removed_or_added_file = False
            from_file = None
            to_file = None
            hunk_to_file_start = 0
            hunk_start_index = 0
            hunk_end_index = 0
            hunk_scanned_line_count = 0
            continue

        if is_not_markdown or is_removed_or_added_file:
            continue

        # from file
        if line.startswith("---"):
            v = line[4:]
            if v.startswith("a/"):
                from_file = v[2:]
            elif v == "/dev/null":
                from_file = None
            else:
                print(f"Unexpected line {i + 1}: {line}", file=sys.stderr)
            continue

        # to file
        if line.startswith("+++"):
            v = line[4:]
            if v.startswith("b/"):
                to_file = v[2:]
            elif v == "/dev/null":
                to_file = None
            else:
                print(f"Unexpected line {i + 1}: {line}", file=sys.stderr)
            continue

        # checks file
        if from_file is None and to_file is None:
            continue

        # Ignore non-markdown files
        if (from_file is not None and not from_file.endswith((".md", ".markdown"))) or (
            to_file is not None and not to_file.endswith((".md", ".markdown"))
        ):
            is_not_markdown = True
            continue

        # file is removed or added
        if from_file is None or to_file is None:
            # ignore removed file and added file
            is_removed_or_added_file = True
            continue

        # hunk
        if line.startswith("@@ "):
            # @@ -old_start,old_count +new_start,new_count @@
            m = re.match(
                r"@@ -\d+(?:,(?P<fc>\d+))? \+(?P<ts>\d+)(?:,(?P<tc>\d+))? @@", line
            )

            if not m:
                print(f"Unexpected line {i + 1}: {line}", file=sys.stderr)
                continue

            from_row_count = int(m.group("fc") or "1")
            to_row_start = int(m.group("ts"))
            to_row_count = int(m.group("tc") or "1")

            hunk_to_file_start = to_row_start
            hunk_start_index = i
            hunk_end_index = i + from_row_count + to_row_count
            continue

    # save last file
    if (
        not is_not_markdown
        and (from_file is not None or to_file is not None)
        and len(diff_lines) > 0
    ):
        diffs.append(FileDiff(from_file, to_file, diff_lines))

    return diffs
