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
    import mkdocs
except Exception:
    BasePlugin = object

from .._git_diff.git_diff import ChangeInfo, WordDiff, run_git_diff
from .._git_diff.parse_porcelain_diff import parse_porcelain_diff
from .._git_diff.parse_unified_diff import parse_unified_diff
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


class MarkdiffPluginConfig(mkdocs.config.base.Config):
    base = mkdocs.config.config_options.Type(str, default="main")
    dir = mkdocs.config.config_options.Type(str, default="docs")
    change_list_file = mkdocs.config.config_options.Type(str, default=None)
    word_diff = mkdocs.config.config_options.Type(bool, default=False)


class MarkdiffPlugin(mkdocs.plugins.BasePlugin[MarkdiffPluginConfig]):
    _git_root_dir: str = None
    _changes: List[ChangeInfo] = []

    def on_pre_build(self, config):
        self._git_root_dir = _get_git_root_dir()

        if self.config["word_diff"]:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.PORCELAIN, self.config["dir"]
            )
            self._changes = parse_porcelain_diff(gitdiff)
        else:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.NONE, self.config["dir"]
            )
            self._changes = parse_unified_diff(gitdiff)

    def on_config(self, config):
        config.extra_css.insert(0, "assets/markdiff/markdiff.css")

        return config

    def on_files(self, files, config):
        # register assets
        files.append(
            mkdocs.structure.files.File(
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
