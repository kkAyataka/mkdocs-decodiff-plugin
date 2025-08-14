from markdiff import hello

def test_markdiff_hello(capsys):
    hello()

    out = capsys.readouterr().out.strip()
    assert out == "Hello, world!"
