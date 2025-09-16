import sys, subprocess

def test_cli():
    r = subprocess.run([sys.executable, "-m", "decodiff"],
                       capture_output=True, text=True)

    assert r.returncode == 0
    assert "Hello, world!" in r.stdout
