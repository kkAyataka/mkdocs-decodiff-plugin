from textwrap import dedent

from mkdocs_decodiff_plugin.markdown_marker import MdMarkContext, _mark_markdown_line

"""
# header
paragraph
> blockquote
* list
    code block
```
fenced coded block
```
___
|h|
|-|
|c|
"""

def test_mark_header():
    """Header"""

    md = dedent("""
        # header
        ## header
        ### header
        #### header
        ##### header
        ###### header
        paragraph
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "H"
    assert ctx.lines[1]._line_type_str() == "H"
    assert ctx.lines[2]._line_type_str() == "H"
    assert ctx.lines[3]._line_type_str() == "H"
    assert ctx.lines[4]._line_type_str() == "H"
    assert ctx.lines[5]._line_type_str() == "H"
    assert ctx.lines[6]._line_type_str() == "P"

def test_mark_header_after_block():
    """Header after block"""

    md = dedent("""
        paragraph
        # header

        > blockquote
        # header

        * list
        # header

            code block
        # header

        ```
        fenced coded block
        ```
        # header

        ___
        # header

        |h|
        |-|
        |c|
        # header
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "P"
    assert ctx.lines[1]._line_type_str() == "H"
    assert ctx.lines[2]._line_type_str() == "E"

    assert ctx.lines[3]._line_type_str() == "Q"
    assert ctx.lines[4]._line_type_str() == "H"
    assert ctx.lines[5]._line_type_str() == "E"

    assert ctx.lines[6]._line_type_str() == "L"
    assert ctx.lines[7]._line_type_str() == "H"
    assert ctx.lines[8]._line_type_str() == "E"

    assert ctx.lines[9]._line_type_str() == "C"
    assert ctx.lines[10]._line_type_str() == "H"
    assert ctx.lines[11]._line_type_str() == "E"

    assert ctx.lines[12]._line_type_str() == "C"
    assert ctx.lines[13]._line_type_str() == "C"
    assert ctx.lines[14]._line_type_str() == "C"
    assert ctx.lines[15]._line_type_str() == "H"
    assert ctx.lines[16]._line_type_str() == "E"

    assert ctx.lines[17]._line_type_str() == "R"
    assert ctx.lines[18]._line_type_str() == "H"
    assert ctx.lines[19]._line_type_str() == "E"

    assert ctx.lines[20]._line_type_str() == "T"
    assert ctx.lines[21]._line_type_str() == "T"
    assert ctx.lines[22]._line_type_str() == "T"
    assert ctx.lines[23]._line_type_str() == "H"

def test_mark_quote():
    """Quote"""

    md = dedent("""
        > quote
        > quote
        quote

        > quote
          quote

        > quote
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "Q"
    assert ctx.lines[1]._line_type_str() == "Q"
    assert ctx.lines[2]._line_type_str() == "Q"
    assert ctx.lines[3]._line_type_str() == "E"
    assert ctx.lines[4]._line_type_str() == "Q"
    assert ctx.lines[5]._line_type_str() == "Q"
    assert ctx.lines[6]._line_type_str() == "E"
    assert ctx.lines[7]._line_type_str() == "Q"

def test_mark_quote_after_block():
    """Quote after block"""

    md = dedent("""
        # header
        > quote

        paragraph
        > quote

        * list
        > quote

            code block
        > quote

        ```
        fenced coded block
        ```
        > quote

        ___
        > quote

        |h|
        |-|
        |c|
        > quote
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "H"
    assert ctx.lines[1]._line_type_str() == "Q"

    assert ctx.lines[2]._line_type_str() == "E"
    assert ctx.lines[3]._line_type_str() == "P"
    assert ctx.lines[4]._line_type_str() == "Q"

    assert ctx.lines[5]._line_type_str() == "E"
    assert ctx.lines[6]._line_type_str() == "L"
    assert ctx.lines[7]._line_type_str() == "Q"

    assert ctx.lines[8]._line_type_str() == "E"
    assert ctx.lines[9]._line_type_str() == "C"
    assert ctx.lines[10]._line_type_str() == "Q"

    assert ctx.lines[11]._line_type_str() == "E"
    assert ctx.lines[12]._line_type_str() == "C"
    assert ctx.lines[13]._line_type_str() == "C"
    assert ctx.lines[14]._line_type_str() == "C"
    assert ctx.lines[15]._line_type_str() == "Q"

    assert ctx.lines[16]._line_type_str() == "E"
    assert ctx.lines[17]._line_type_str() == "R"
    assert ctx.lines[18]._line_type_str() == "Q"

    assert ctx.lines[19]._line_type_str() == "E"
    assert ctx.lines[20]._line_type_str() == "T"
    assert ctx.lines[21]._line_type_str() == "T"
    assert ctx.lines[22]._line_type_str() == "T"
    assert ctx.lines[23]._line_type_str() == "Q"

def test_mark_paragraph():
    """Paragraph"""

    md = dedent("""
        paragraph
        paragraph

        paragraph
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "P"
    assert ctx.lines[1]._line_type_str() == "P"
    assert ctx.lines[2]._line_type_str() == "E"
    assert ctx.lines[3]._line_type_str() == "P"

def test_mark_paragraph_after_block():
    """Paragraph after block"""

    md = dedent("""
        # header
        paragraph

        > quote

        paragraph

        * list

        paragraph

            code block
        paragraph

        ```
        fenced coded block
        ```
        paragraph

        ___
        paragraph

        |h|
        |-|
        |c|
        paragraph
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "H"
    assert ctx.lines[1]._line_type_str() == "P"
    assert ctx.lines[2]._line_type_str() == "E"

    assert ctx.lines[3]._line_type_str() == "Q"
    assert ctx.lines[4]._line_type_str() == "E"
    assert ctx.lines[5]._line_type_str() == "P"
    assert ctx.lines[6]._line_type_str() == "E"

    assert ctx.lines[7]._line_type_str() == "L"
    assert ctx.lines[8]._line_type_str() == "E"
    assert ctx.lines[9]._line_type_str() == "P"
    assert ctx.lines[10]._line_type_str() == "E"

    assert ctx.lines[11]._line_type_str() == "C"
    assert ctx.lines[12]._line_type_str() == "P"
    assert ctx.lines[13]._line_type_str() == "E"

    assert ctx.lines[14]._line_type_str() == "C"
    assert ctx.lines[15]._line_type_str() == "C"
    assert ctx.lines[16]._line_type_str() == "C"
    assert ctx.lines[17]._line_type_str() == "P"
    assert ctx.lines[18]._line_type_str() == "E"

    assert ctx.lines[19]._line_type_str() == "R"
    assert ctx.lines[20]._line_type_str() == "P"
    assert ctx.lines[21]._line_type_str() == "E"

    assert ctx.lines[22]._line_type_str() == "T"
    assert ctx.lines[23]._line_type_str() == "T"
    assert ctx.lines[24]._line_type_str() == "T"
    assert ctx.lines[25]._line_type_str() == "P"

def test_mark_list():
    """List"""

    md = dedent("""
        * list
        * list
        list
        * list
          list
            - list
            - list
              list

        * list
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "L"
    assert ctx.lines[1]._line_type_str() == "L"
    assert ctx.lines[2]._line_type_str() == "L"
    assert ctx.lines[3]._line_type_str() == "L"
    assert ctx.lines[4]._line_type_str() == "L"
    assert ctx.lines[5]._line_type_str() == "L"
    assert ctx.lines[6]._line_type_str() == "L"
    assert ctx.lines[7]._line_type_str() == "L"
    assert ctx.lines[8]._line_type_str() == "E"
    assert ctx.lines[9]._line_type_str() == "L"

def test_mark_list_after_block():
    """List after block"""

    md = dedent("""
        # header
        * list

        paragraph
        * list

        > blockquote
        * list

            code block
        * list

        ```
        fenced coded block
        ```
        * list

        ___
        * list

        |h|
        |-|
        |c|
        * list
        """).strip()

    ctx = MdMarkContext()
    for no, line in enumerate(md.splitlines(), start=1):
        _mark_markdown_line(ctx, no, line)

    assert ctx.lines[0]._line_type_str() == "H"
    assert ctx.lines[1]._line_type_str() == "L"

    assert ctx.lines[2]._line_type_str() == "E"
    assert ctx.lines[3]._line_type_str() == "P"
    assert ctx.lines[4]._line_type_str() == "L"

    assert ctx.lines[5]._line_type_str() == "E"
    assert ctx.lines[6]._line_type_str() == "Q"
    assert ctx.lines[7]._line_type_str() == "L"

    assert ctx.lines[8]._line_type_str() == "E"
    assert ctx.lines[9]._line_type_str() == "C"
    assert ctx.lines[10]._line_type_str() == "L"

    assert ctx.lines[11]._line_type_str() == "E"
    assert ctx.lines[12]._line_type_str() == "C"
    assert ctx.lines[13]._line_type_str() == "C"
    assert ctx.lines[14]._line_type_str() == "C"
    assert ctx.lines[15]._line_type_str() == "L"

    assert ctx.lines[16]._line_type_str() == "E"
    assert ctx.lines[17]._line_type_str() == "R"
    assert ctx.lines[18]._line_type_str() == "L"

    assert ctx.lines[19]._line_type_str() == "E"
    assert ctx.lines[20]._line_type_str() == "T"
    assert ctx.lines[21]._line_type_str() == "T"
    assert ctx.lines[22]._line_type_str() == "T"
    assert ctx.lines[23]._line_type_str() == "L"
