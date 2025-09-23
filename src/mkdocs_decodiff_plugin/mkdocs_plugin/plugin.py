"""
MkDocs plugin that annotates Markdown files before the build, then restores them after.

Configure in mkdocs.yml like:

plugins:
  - decodiff:
      base: v1.0.0
      dir: docs
      change_list_file: docs/changes.md
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import mkdocs
    from mkdocs.structure.pages import Page
except Exception:
    BasePlugin = object

from .._git_diff.git_diff import FileDiff, WordDiff, run_git_diff
from .._git_diff.parse_porcelain_diff import parse_porcelain_diff
from .._git_diff.parse_unified_diff import parse_unified_diff
from ..decodiff import (
    FileChange,
    LineChange,
    make_file_changes,
)


@dataclass
class ChangeListItem:
    file_path: str
    is_new: bool = False
    changes: List[LineChange] = field(default_factory=list)


_DECODIFF_CHANGE_LIST_START = "<!-- decodiff: Written by decodiff from here -->"
_DECODIFF_CHANGE_LIST_END = "<!-- decodiff: end -->"


def _make_change_list_md(
    change_list_file_path: str, file_changes: List[FileChange]
) -> str:
    md = ""

    change_list_file_dir = os.path.dirname(change_list_file_path)
    for file_change in file_changes:
        # ignore removed file
        if file_change.is_removed:
            continue

        relpath = os.path.relpath(file_change.file_path, change_list_file_dir)
        md += "\n" if not md else ""
        md += f"## [{relpath}]({relpath})\n\n"

        # added file
        if file_change.is_added:
            md += "* New\n"
            continue

        # changed file
        for line_change in file_change.line_changes:
            text = line_change.line.strip()
            text = f"{text[:40]}{'...' if len(text) > 40 else ''}"

            md += f"* [{text}]({relpath}#{line_change.anchor})\n"

    return md


def _get_git_root_dir() -> Optional[str]:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return root
    except subprocess.CalledProcessError:
        return None


class DecodiffPluginConfig(mkdocs.config.base.Config):
    base = mkdocs.config.config_options.Type(str, default="main")
    dir = mkdocs.config.config_options.Type(str, default="docs")
    change_list_file = mkdocs.config.config_options.Type(str, default="docs/changes.md")
    word_diff = mkdocs.config.config_options.Type(bool, default=False)


class DecodiffPlugin(mkdocs.plugins.BasePlugin[DecodiffPluginConfig]):
    _git_root_dir: str = None
    _file_changes: List[FileChange] = []
    _file_diffs: List[FileDiff] = []
    _change_list_file_path: str = None
    _change_list_md: str = None

    def on_pre_build(self, config):
        # git root
        self._git_root_dir = _get_git_root_dir()
        if self._git_root_dir is None:
            # Here is not a git folder
            return

        # get diff
        file_diffs: List[FileDiff] = []
        if self.config["word_diff"]:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.PORCELAIN, self.config["dir"]
            )
            file_diffs = parse_porcelain_diff(gitdiff)
        else:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.NONE, self.config["dir"]
            )
            file_diffs = parse_unified_diff(gitdiff)
        self._file_diffs = file_diffs

        # make file changes
        self._file_changes = make_file_changes(self._git_root_dir, self._file_diffs)

        # change list
        change_list_file_path = self.config["change_list_file"]
        if change_list_file_path is not None and change_list_file_path:
            if os.path.isabs(change_list_file_path):
                self._change_list_file_path = change_list_file_path
            else:
                self._change_list_file_path = os.path.join(
                    os.path.dirname(config.config_file_path), change_list_file_path
                )

            if not os.path.exists(self._change_list_file_path):
                print(
                    f"Change list file is not found: {self.config['change_list_file']}",
                    file=sys.stderr,
                )
            else:
                self._change_list_md = _make_change_list_md(
                    self._change_list_file_path, self._file_changes
                )

    def on_config(self, config):
        config.extra_css.insert(0, "assets/decodiff/decodiff.css")

        return config

    def on_files(self, files, config):
        # register assets
        files.append(
            mkdocs.structure.files.File(
                path="decodiff.css",
                src_dir=os.path.join(os.path.dirname(__file__), "assets"),
                dest_dir=f"{config.site_dir}/assets/decodiff",
                use_directory_urls=False,
            )
        )

        return files

    def on_page_markdown(self, markdown: str, page: Page, config, files):
        file_path = os.path.join(page.file.src_dir, page.file.src_path)

        md = markdown

        # change list file
        if (
            self._change_list_file_path is not None
            and file_path == self._change_list_file_path
        ):
            # search decodiff comment
            p = re.compile(
                rf"{_DECODIFF_CHANGE_LIST_START}.*?{_DECODIFF_CHANGE_LIST_END}",
                re.DOTALL,
            )
            change_list_md = f"{_DECODIFF_CHANGE_LIST_START}\n\n{self._change_list_md}{_DECODIFF_CHANGE_LIST_END}\n"

            # try replace
            md, num = p.subn(change_list_md, md)
            if num <= 0:
                # if the decodiff comment is not found, add to the tail
                md += "\n" + change_list_md

        # chagned file
        for file_change in self._file_changes:
            # checks whether the markdown file has changes
            if file_path == file_change.file_path:
                # Leading empty lines and metadata lines have been removed.
                # Count how many lines were removed before the current first line appears
                first_line = markdown.partition("\n")[0]
                raw_md = page.file.content_string
                offset = 0
                while True:
                    # read 1 line
                    line, _, raw_md = raw_md.partition("\n")
                    if line == first_line:
                        break
                    elif raw_md == "":
                        # file is end
                        break
                    else:
                        # It is removed line from raw content
                        # It is metadata or empty lines at head
                        offset += 1

                # replave changed lines
                md_lines = markdown.splitlines()
                for line_change in file_change.line_changes:
                    md_lines[line_change.line_no - offset - 1] = line_change.tagged_line
                md = "\n".join(md_lines)

        return md
