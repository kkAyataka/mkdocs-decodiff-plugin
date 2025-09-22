import re
import sys
from typing import List

from .git_diff import FileDiff, LineDiff


def parse_porcelain_diff(diff_text: str) -> List[FileDiff]:
    """Parses a porcelain diff text."""

    changed: List[FileDiff] = []
    anchor_no = 0

    is_completed = False

    from_file = None
    to_file = None
    line_info_list: List[LineDiff] = []

    hunk_to_file_start = 0
    hunk_start = 0
    hunk_line_count = 0
    hunk_scanned_line_count = 0
    hunk_col_pos = 0

    for i, line in enumerate(diff_text.splitlines()):
        # in hunk
        if hunk_start < i and hunk_scanned_line_count < hunk_line_count:
            if line == "~":
                hunk_scanned_line_count += 1
                # hunk end
                if hunk_scanned_line_count == hunk_line_count:
                    hunk_to_file_start = 0
                    hunk_start = 0
                    hunk_line_count = 0
                    hunk_scanned_line_count = 0
                    hunk_col_pos = 0
                    # changed.append(ChangeInfo(from_file, to_file, line_info_list))
            elif line.startswith(" "):
                hunk_col_pos += len(line) - 1
            elif line.startswith("+"):
                line_info_list.append(
                    LineDiff(
                        hunk_to_file_start + hunk_scanned_line_count,
                        hunk_col_pos,
                        hunk_col_pos + len(line) - 1,
                        anchor_no,
                    )
                )
                anchor_no += 1
            elif line.startswith("-"):
                # ignore removed words
                pass

            continue

        # start file
        if line.startswith("diff --git "):
            if from_file is not None or to_file is not None:
                # previous file end
                changed.append(FileDiff(from_file, to_file, line_info_list))
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
            is_completed = True
            continue

        # file is deleted or added
        if from_file is None or to_file is None:
            is_completed = True
            changed.append(FileDiff(from_file, to_file, []))
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
            from_count = int(m.group("fc") or "1")
            to_start = int(m.group("ts"))
            to_count = int(m.group("tc") or "1")

            hunk_to_file_start = to_start
            hunk_start = i
            hunk_line_count = max(from_count, to_count)
            continue

    if from_file is not None or to_file is not None:
        # previous file end
        changed.append(FileDiff(from_file, to_file, line_info_list))

    # remove empty entries
    return changed
