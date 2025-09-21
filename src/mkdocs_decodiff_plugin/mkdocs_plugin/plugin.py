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
from dataclasses import dataclass, field
from typing import List

try:
    import mkdocs
    from mkdocs.structure.pages import Page
except Exception:
    BasePlugin = object

from .._git_diff.git_diff import ChangeInfo, WordDiff, run_git_diff
from .._git_diff.parse_porcelain_diff import parse_porcelain_diff
from .._git_diff.parse_unified_diff import parse_unified_diff
from ..decodiff import embed_decodiff_tags, embed_decodiff_tags2
from ..markdown_marker import mark_markdown, mark_markdown_lines


@dataclass
class ChangedFile:
    file_path: str

    is_new: bool = False
    changes: List[any] = field(default_factory=list)


_DECODIFF_CHANGE_LIST_START = "<!-- decodiff: Written by decodiff from here -->"
_DECODIFF_CHANGE_LIST_END = "<!-- decodiff: end -->"


def _filter_changes(root_path: str, changes: List[ChangeInfo]):
    changed_files = []
    for c in changes:
        if c.to_file is None:
            # ignore delted files
            continue

        file_path = os.path.join(root_path, c.to_file)

        if c.from_file is None:
            changed_files.append(ChangedFile(file_path=file_path, is_new=True))
            continue

        marked_lines = mark_markdown(file_path)
        changed = embed_decodiff_tags2(marked_lines, c)

        changed_files.append(ChangedFile(file_path=file_path, changes=changed))

    return changed_files


def _get_git_root_dir():
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
    _changes: List[ChangeInfo] = []
    _change_list_file: str = None
    _change_list_md: str = None

    def on_pre_build(self, config):
        # git root
        self._git_root_dir = _get_git_root_dir()

        # get diff data
        changes: List[ChangeInfo] = []
        if self.config["word_diff"]:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.PORCELAIN, self.config["dir"]
            )
            changes = parse_porcelain_diff(gitdiff)
        else:
            gitdiff = run_git_diff(
                self.config["base"], WordDiff.NONE, self.config["dir"]
            )
            changes = parse_unified_diff(gitdiff)
        self._changes = changes

        # create change=list=file path and initial file
        change_list_file = self.config["change_list_file"]
        if not change_list_file and change_list_file != "":
            self._change_list_file = os.path.join(
                os.path.dirname(config.config_file_path), change_list_file
            )
            if not os.path.exists(self._change_list_file):
                with open(self._change_list_file, "w", encoding="utf-8") as f:
                    f.write("# Changes\n\n")
                    f.write(f"{_DECODIFF_CHANGE_LIST_START}\n\n")
                    f.write(f"{_DECODIFF_CHANGE_LIST_END}\n")

            filtered_changes = _filter_changes(self._git_root_dir, changes)
            md = ""
            for c in filtered_changes:
                relpath = os.path.relpath(
                    c.file_path, os.path.dirname(self._change_list_file)
                )
                if c.is_new:
                    md += f"\n## [{relpath}]({relpath})\n\n"
                    md += "* New\n"
                else:
                    md += f"## [{relpath}]({relpath})\n\n"
                    for change in c.changes:
                        text = change.line.strip()
                        text = f"{text[:40]}{'...' if len(text) > 40 else ''}"
                        md += f"* [{text}]({relpath}#{change.anchor})\n"
            self._change_list_md = md

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
        if not self._chane_list_file and file_path == self._change_list_file:
            # search decodiff comment
            p = re.compile(
                rf"{_DECODIFF_CHANGE_LIST_START}.*?{_DECODIFF_CHANGE_LIST_END}",
                re.DOTALL,
            )
            list_md = f"{_DECODIFF_CHANGE_LIST_START}\n\n{self._change_list_md}{_DECODIFF_CHANGE_LIST_END}\n"

            # try replace
            md, num = p.subn(list_md, md)
            if num <= 0:
                # if the decodiff comment is not found, add to the tail
                md += "\n" + list_md

        for change in self._changes:
            to_file = os.path.join(self._git_root_dir, change.to_file)
            # checks whether the markdown file has changes
            if file_path == to_file:
                # Leading empty lines and metadata lines have been removed.
                # Count how many lines were removed before the current first line appears
                first_line = markdown.partition("\n")[0]
                offset = 0
                raw_md = page.file.content_string
                while True:
                    line, _, raw_md = raw_md.partition("\n")
                    if line == first_line:
                        break
                    elif raw_md == "":
                        break
                    else:
                        offset -= 1

                # embed markdif tag and make new markdown
                marked_lines = mark_markdown_lines(markdown.splitlines())
                md = embed_decodiff_tags(marked_lines, change, offset)

        return md
