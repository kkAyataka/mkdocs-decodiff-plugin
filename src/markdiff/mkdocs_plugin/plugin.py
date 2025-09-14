"""
MkDocs plugin that annotates Markdown files before the build, then restores them after.

Configure in mkdocs.yml like:

plugins:
  - markdiff:
      base: v1.0.0
      dir: docs
      change_list_file: docs/changes.md
"""

from __future__ import annotations

import os
import subprocess
from typing import List

try:
    from mkdocs.plugins import BasePlugin
    from mkdocs.structure.files import File
except Exception:
    BasePlugin = object

from .._git_diff import ChangeInfo, WordDiff, parse_porcelain_diff, run_git_diff
from ..markdiff import _embed_markdiff_tags
from ..markdown_marker import mark_markdown_lines


def _get_git_root_dir():
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return root
    except subprocess.CalledProcessError:
        return None


class MarkdiffPlugin(BasePlugin):
    _git_root_dir: str = None
    _changes: List[ChangeInfo] = []

    def on_pre_build(self, config):
        self._git_root_dir = _get_git_root_dir()

        gitdiff = run_git_diff(
            self.config["base"], WordDiff.PORCELAIN, self.config["dir"]
        )
        self._changes = parse_porcelain_diff(gitdiff)

    def on_config(self, config):
        config.extra_css.insert(0, "assets/markdiff/markdiff.css")

        return config

    def on_files(self, files, config):
        # register assets
        files.append(
            File(
                path="markdiff.css",
                src_dir=os.path.join(os.path.dirname(__file__), "assets"),
                dest_dir=f"{config.site_dir}/assets/markdiff",
                use_directory_urls=False,
            )
        )

        return files

    def on_page_markdown(self, markdown: str, page, config, files):
        file_path = os.path.join(page.file.src_dir, page.file.src_path)

        md = markdown
        for change in self._changes:
            to_file = os.path.join(self._git_root_dir, change.to_file)
            # checks whether the markdown file has changes
            if file_path == to_file:
                # embed markdif tag and make new markdown
                marked_lines = mark_markdown_lines(markdown.splitlines())
                md = _embed_markdiff_tags(marked_lines, change)

        return md
