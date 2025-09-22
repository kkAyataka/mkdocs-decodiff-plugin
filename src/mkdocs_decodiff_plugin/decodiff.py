import re
from dataclasses import dataclass
from typing import List


@dataclass
class ChangedItem:
    line_no: int
    line: str
    tagged_line: str
    anchor: str


def embed_decodiff_tags2(marked_lines, change_info) -> List[ChangedItem]:
    changes: List[ChangedItem] = []
    for i in change_info.changed_lines:
        marked_line = marked_lines[i.line_no - 1]
        if (
            marked_line.is_meta()
            or marked_line.is_empty()
            or marked_line.is_code_block()
            or marked_line.is_h_rule()
            or marked_line.is_table()
        ):
            continue

        offset = 0
        if i.col_start == 0:
            if m := re.search(r"^#+ ", marked_line.line):
                offset = m.end()
            elif m := re.search(r"^\s*[*\-+] (\[[ xX]\] )?", marked_line.line):
                offset = m.end()
            elif m := re.search(r"^\s*\d+[.)] ", marked_line.line):
                offset = m.end()
            elif m := re.search(r"^> ", marked_line.line):
                offset = m.end()

        start = i.col_start + offset
        end = i.col_end
        anchor = f"decodiff-anchor-{i.anchor_no}"
        new_line = (
            marked_line.line[:start]
            + f'<span id="{anchor}" class="decodiff">'
            + marked_line.line[start:end]
            + "</span>"
            + marked_line.line[end:]
        )
        changes.append(
            ChangedItem(
                line_no=i.line_no,
                line=marked_line.line,
                tagged_line=new_line,
                anchor=anchor,
            )
        )

    return changes


def embed_decodiff_tags(marked_lines, change_info, start_offset=0) -> str:
    changed_line_iter = iter(change_info.changed_lines)
    changed_line = next(changed_line_iter, None)
    new_lines = []

    # skip ignored lines
    while True:
        if changed_line.line_no <= -start_offset:
            changed_line = next(changed_line_iter, None)
        else:
            break

    for i, md_line in enumerate(marked_lines, start=1):
        if changed_line is None:
            new_lines.append(md_line.line)
            continue

        if i == changed_line.line_no + start_offset:
            if (
                md_line.is_empty()
                or md_line.is_code_block()
                or md_line.is_h_rule()
                or md_line.is_table()
            ):
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
                + f'<span id="decodiff-anchor-{anchor_no}" class="decodiff">'
                + md_line.line[start:end]
                + "</span>"
                + md_line.line[end:]
            )
            new_lines.append(new_line)

            changed_line = next(changed_line_iter, None)
        else:
            new_lines.append(md_line.line)

    return "\n".join(new_lines)
