import re
from dataclasses import dataclass
from typing import List, Optional

from ._git_diff.git_diff import FileDiff, LineDiff
from .markdown_marker import MdLine


@dataclass
class ChangedLine:
    line_no: int
    line: str
    tagged_line: str
    anchor: str


def _embed_decodiff_tag_line(
    marked_line: MdLine, line_diff: LineDiff
) -> Optional[ChangedLine]:
    if (
        marked_line.is_meta()
        or marked_line.is_empty()
        or marked_line.is_code_block()
        or marked_line.is_h_rule()
        or marked_line.is_table()
    ):
        return None

    col_offset = 0
    if line_diff.col_start == 0:
        # heading
        if m := re.search(r"^#+ ", marked_line.line):
            col_offset = m.end()
        # list
        elif m := re.search(r"^\s*[*\-+] (\[[ xX]\] )?", marked_line.line):
            col_offset = m.end()
        # numbered list
        elif m := re.search(r"^\s*\d+[.)] ", marked_line.line):
            col_offset = m.end()
        # quote
        elif m := re.search(r"^> ", marked_line.line):
            col_offset = m.end()

    start = line_diff.col_start + col_offset
    end = line_diff.col_end
    anchor = f"decodiff-anchor-{line_diff.anchor_no}"
    new_line = (
        marked_line.line[:start]
        + f'<span id="{anchor}" class="decodiff">'
        + marked_line.line[start:end]
        + "</span>"
        + marked_line.line[end:]
    )

    return ChangedLine(line_diff.line_no, marked_line.line, new_line, anchor)


def embed_decodiff_tags2(marked_lines: List[MdLine], diff_info: FileDiff) -> List[ChangedLine]:
    changes: List[ChangedLine] = []
    for line_diff in diff_info.line_diffs:
        marked_line = marked_lines[line_diff.line_no - 1]
        changd_line = _embed_decodiff_tag_line(marked_line, line_diff)
        if changd_line is not None:
            changes.append(changd_line)

    return changes


def embed_decodiff_tags(marked_lines: List[MdLine], diff_info: FileDiff, start_offset=0) -> str:
    line_diff_iter = iter(diff_info.line_diffs)
    line_diff = next(line_diff_iter, None)
    new_lines = []

    # skip ignored lines
    while True:
        if line_diff.line_no <= -start_offset:
            line_diff = next(line_diff_iter, None)
        else:
            break

    for line_no, marked_line in enumerate(marked_lines, start=1):
        if line_diff is None:
            new_lines.append(marked_line.line)
            continue

        if line_no == line_diff.line_no + start_offset:
            changed = _embed_decodiff_tag_line(marked_line, line_diff)
            if changed is not None:
                new_lines.append(changed.tagged_line)
            else:
                new_lines.append(marked_line.line)

            line_diff = next(line_diff_iter, None)
        else:
            new_lines.append(marked_line.line)

    return "\n".join(new_lines)
