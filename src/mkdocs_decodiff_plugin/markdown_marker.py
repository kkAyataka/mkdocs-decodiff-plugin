import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class MdLineType(Enum):
    """Markdown line type"""

    EMPTY = 1
    HEADING = 2
    QUOTE = 4
    LIST = 8
    CODE_BLOCK = 16
    H_RULE = 32
    TABLE = 64
    PARAGRAPH = 128

    META = 1024


@dataclass(frozen=True)
class MdLine:
    """Markdown line"""

    line: str
    line_type: int

    def is_empty(self) -> bool:
        return self.line_type & MdLineType.EMPTY.value

    def is_heading(self) -> bool:
        return self.line_type & MdLineType.HEADING.value

    def is_quote(self) -> bool:
        return self.line_type & MdLineType.QUOTE.value

    def is_list(self) -> bool:
        return self.line_type & MdLineType.LIST.value

    def is_code_block(self) -> bool:
        return self.line_type & MdLineType.CODE_BLOCK.value

    def is_h_rule(self) -> bool:
        return self.line_type & MdLineType.H_RULE.value

    def is_table(self) -> bool:
        return self.line_type & MdLineType.TABLE.value

    def is_paragraph(self) -> bool:
        return self.line_type & MdLineType.PARAGRAPH.value

    def is_meta(self) -> bool:
        return self.line_type & MdLineType.META.value

    def _line_type_str(self) -> str:
        types = []
        if self.line_type & MdLineType.EMPTY.value:
            types.append("E")
        if self.line_type & MdLineType.HEADING.value:
            types.append("H")
        if self.line_type & MdLineType.QUOTE.value:
            types.append("Q")
        if self.line_type & MdLineType.LIST.value:
            types.append("L")
        if self.line_type & MdLineType.CODE_BLOCK.value:
            types.append("C")
        if self.line_type & MdLineType.H_RULE.value:
            types.append("R")
        if self.line_type & MdLineType.TABLE.value:
            types.append("T")
        if self.line_type & MdLineType.PARAGRAPH.value:
            types.append("P")
        if self.line_type & MdLineType.META.value:
            types.append("M")

        return ",".join(types)

    def __str__(self) -> str:
        return f"{self._line_type_str()}: {self.line}"


@dataclass
class MdMarkContext:
    """Marking (Parsing) context"""

    lines: list[MdLine] = field(default_factory=list)
    in_quote = False
    in_list = False
    in_code_block = False
    in_indent_code_block = False
    in_table = False
    in_meta = False

    def set(
        self,
        in_quote=False,
        in_list=False,
        in_code_block=False,
        in_indent_code_block=False,
        in_table=False,
        in_meta=False,
    ):
        self.in_quote = in_quote
        self.in_list = in_list
        self.in_code_block = in_code_block
        self.in_indent_code_block = in_indent_code_block
        self.in_table = in_table
        self.in_meta = in_meta


def _mark_markdown_line(ctx: MdMarkContext, line_no: int, line: str):
    """Mark a single line"""

    line_type = 0

    if ctx.in_indent_code_block and not line.startswith("    "):
        ctx.in_indent_code_block = False
        ctx.in_code_block = False
    # Metadata lines of MkDocs
    if line_no == 1 and re.search(r"^---\s*$", line):
        ctx.in_meta = True
        line_type |= MdLineType.META.value
    elif ctx.in_meta:
        line_type |= MdLineType.META.value
        if re.search(r"^(---|...)\s*$", line):
            ctx.in_meta = False
    # blocks
    # header
    elif re.search(r"^#+ ", line):
        if not ctx.in_code_block:
            line_type |= MdLineType.HEADING.value
            ctx.set()
    # blockquotes
    elif re.search(r"^> ", line):
        if not ctx.in_code_block:
            line_type |= MdLineType.QUOTE.value
            ctx.set(in_quote=True)
    # bulleted list
    elif m := re.match(r"^(\s*)[*\-+] (\[[ xX]\] )?", line):
        if m.group(1) == "":
            line_type |= MdLineType.LIST.value
            ctx.set(in_list=True)
        elif ctx.in_list:
            line_type |= MdLineType.LIST.value
        elif ctx.in_quote:
            line_type |= MdLineType.QUOTE.value
        elif ctx.in_code_block:
            line_type |= MdLineType.CODE_BLOCK.value

        if not ctx.in_code_block:
            if m.group(1) == "":
                line_type |= MdLineType.LIST.value
                ctx.set(in_list=True)
            elif ctx.in_list:
                line_type |= MdLineType.LIST.value
                ctx.set(in_list=True)

    # numbered list
    elif m := re.match(r"^(\s*)\d+[.)] ", line):
        if not ctx.in_code_block:
            if m.group(1) == "":
                line_type |= MdLineType.LIST.value
                ctx.set(in_list=True)
            elif ctx.in_list:
                line_type |= MdLineType.LIST.value
                ctx.set(in_list=True)

    # fenced code block
    elif re.search(r"^\s*```", line):
        line_type |= MdLineType.CODE_BLOCK.value
        ctx.in_code_block = not ctx.in_code_block

        if ctx.in_code_block:
            ctx.set(in_code_block=ctx.in_code_block)
    # indent code block
    elif re.search(r"^    .*", line):
        is_empty_prev_line = (
            ctx.lines and ctx.lines[-1].line_type & MdLineType.EMPTY.value
        )
        if is_empty_prev_line:
            line_type |= MdLineType.CODE_BLOCK.value
            ctx.set(in_code_block=True, in_indent_code_block=True)
        elif ctx.in_list:
            line_type |= MdLineType.LIST.value
        elif ctx.in_quote:
            line_type |= MdLineType.QUOTE.value
        else:
            line_type |= MdLineType.CODE_BLOCK.value
            ctx.set(in_code_block=True, in_indent_code_block=True)
    # horizontal rule
    elif re.search(r"^([\*\-_]\s*){3,}$", line):
        if not ctx.in_code_block:
            line_type |= MdLineType.H_RULE.value
            ctx.set()
    # table
    elif re.search(r"^(\|[ \t\-:|]*|[-:][-:| ]*)$", line):
        if not ctx.in_code_block:
            line_type |= MdLineType.TABLE.value
            ctx.set(in_table=True)

            if ctx.lines:
                prev_line = ctx.lines[-1]
                if re.search(r"^(\|)?.*\|.*", prev_line.line):
                    ctx.lines[-1] = MdLine(
                        prev_line.line, prev_line.line_type | MdLineType.TABLE.value
                    )
    # table row
    elif re.search(r"^(\|)?.*\|.*", line):
        if not ctx.in_code_block and ctx.in_table:
            line_type |= MdLineType.TABLE.value
    # empty
    elif re.search(r"^\s*$", line):
        line_type |= MdLineType.EMPTY.value
    # paragraph
    elif re.search(r"^[^\s]", line):
        is_empty_prev_line = (
            ctx.lines and ctx.lines[-1].line_type & MdLineType.EMPTY.value
        )
        if ctx.in_code_block and not is_empty_prev_line:
            line_type |= MdLineType.CODE_BLOCK.value
        elif ctx.in_list and not is_empty_prev_line:
            line_type |= MdLineType.LIST.value
        elif ctx.in_quote and not is_empty_prev_line:
            line_type |= MdLineType.QUOTE.value
        else:
            if is_empty_prev_line:
                ctx.set()
            line_type |= MdLineType.PARAGRAPH.value
    elif re.search(r"^\s+[^\s]", line):
        if ctx.in_code_block:
            line_type |= MdLineType.CODE_BLOCK.value
        elif ctx.in_list:
            line_type |= MdLineType.LIST.value
        elif ctx.in_quote:
            line_type |= MdLineType.QUOTE.value

    ctx.lines.append(MdLine(line, line_type))


def mark_markdown_lines(lines: List[str]) -> List[MdLine]:
    """Mark markdown lines"""

    ctx = MdMarkContext()
    for line_no, line in enumerate(lines, start=1):
        _mark_markdown_line(ctx, line_no, line)

    return ctx.lines


def mark_markdown(file_path: str) -> List[MdLine]:
    """Mark markdown"""

    lines: list[MdLine] = []
    with open(file_path, "r", encoding="utf-8") as f:
        ctx = MdMarkContext()
        for line_no, line in enumerate(f, start=1):
            _mark_markdown_line(ctx, line_no, line.rstrip("\n"))

        lines = ctx.lines
    return lines
