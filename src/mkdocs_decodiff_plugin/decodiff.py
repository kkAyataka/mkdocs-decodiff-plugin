import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from ._git_diff.git_diff import FileDiff, LineDiff
from .markdown_marker import MdLine, mark_markdown


@dataclass
class LineChange:
    line_no: int
    line: str
    tagged_line: str
    anchor: str


@dataclass
class FileChange:
    file_path: str
    is_removed: bool = False
    is_added: bool = False
    line_changes: List[LineChange] = field(default_factory=list)


def _embed_decodiff_tag_line(
    marked_line: MdLine, line_diff: LineDiff
) -> Optional[LineChange]:
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

    return LineChange(line_diff.line_no, marked_line.line, new_line, anchor)


def embed_decodiff_tags(
    marked_lines: List[MdLine], file_diff: FileDiff
) -> List[LineChange]:
    changes: List[LineChange] = []
    for line_diff in file_diff.line_diffs:
        marked_line = marked_lines[line_diff.line_no - 1]
        changd_line = _embed_decodiff_tag_line(marked_line, line_diff)
        if changd_line is not None:
            changes.append(changd_line)

    return changes


def make_file_changes(
    git_root_path: str, file_diffs: List[FileDiff]
) -> List[FileChange]:
    file_changes: List[FileChange] = []
    for file_diff in file_diffs:
        # removed file
        if file_diff.to_file is None:
            file_path = os.path.join(git_root_path, file_diff.from_file)
            file_changes.append(FileChange(file_path, is_removed=True))
            continue

        file_path = os.path.join(git_root_path, file_diff.to_file)

        # added file
        if file_diff.from_file is None:
            file_changes.append(FileChange(file_path, is_added=True))
            continue

        # changed file
        marked_lines = mark_markdown(file_path)
        line_changes = embed_decodiff_tags(marked_lines, file_diff)
        file_changes.append(FileChange(file_path, line_changes=line_changes))

    return file_changes
