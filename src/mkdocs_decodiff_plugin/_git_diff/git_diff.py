import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


@dataclass
class LineDiff:
    line_no: int
    col_start: int
    col_end: int
    anchor_no: int


@dataclass
class FileDiff:
    from_file: Optional[str] = None
    to_file: Optional[str] = None
    line_diffs: List[LineDiff] = field(default_factory=list)


class WordDiff(Enum):
    """--word-diff option type of git-diff"""

    # COLOR = 1
    # PLAIN = 2
    PORCELAIN = 3
    NONE = 0

    def __str__(self):
        if self == WordDiff.PORCELAIN:
            return "porcelain"
        else:
            return "none"


def run_git_diff(base: str, word_diff: WordDiff, target_dir: Optional[str]) -> str:
    """Runs git diff"""

    args = [
        "git",
        "diff",
        "--no-color",
        "--ignore-all-space",
        f"--word-diff={word_diff}",
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
