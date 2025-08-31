from __future__ import annotations

"""
MkDocs plugin that annotates Markdown files before the build, then restores them after.

Configure in mkdocs.yml like:

plugins:
  - search
  - markdiff:
      base: v1.0.0
      dir: docs
      change_list_file: docs/diff.md
"""

import os
from typing import Dict, List, Optional, Tuple

try:
    from mkdocs.plugins import BasePlugin
except Exception:  # pragma: no cover - mkdocs not available in test env
    BasePlugin = object  # type: ignore

from .markdiff import (
    _run_git_diff,
    _parse_diff,
    _annotate_lines,
    _read_text,
    _write_text,
)


class MarkdiffPlugin(BasePlugin):  # type: ignore[misc]
    config_scheme = ()

    def __init__(self) -> None:
        # path -> original lines
        self._backups: Dict[str, List[str]] = {}

    def _annotate_before_build(
        self,
        base: str,
        target_dir: Optional[str],
        change_list_file: Optional[str],
        unified: int = 0,
    ) -> None:
        diff = _run_git_diff(base, target_dir, unified)
        changed_map = _parse_diff(diff)
        # file -> list of (anchor_id, label)
        grouped_links: Dict[str, List[Tuple[str, str]]] = {}

        for file_path, changed_lines in changed_map.items():
            fs_path = os.path.join(os.getcwd(), file_path)
            if not os.path.exists(fs_path):
                continue
            try:
                lines = _read_text(fs_path)
            except UnicodeDecodeError:
                continue

            # backup and write annotated
            self._backups[fs_path] = list(lines)
            new_lines, anchors = _annotate_lines(lines, changed_lines)
            _write_text(fs_path, new_lines)
            for _line_no, anchor_id, label in anchors:
                grouped_links.setdefault(file_path, []).append((anchor_id, label))

        if change_list_file and grouped_links:
            from datetime import date
            output: List[str] = ["# Changes\n\n"]
            output.append(f"* Generated on: {date.today().isoformat()}\n")
            output.append(f"* Base commit: {base}\n\n")

            for file_path, anchors in grouped_links.items():
                output.append(f"## [{file_path}]({file_path})\n\n")
                for anchor_id, label in anchors:
                    link_label = label if label.strip() else anchor_id
                    link = f"{file_path}#{anchor_id}"
                    output.append(f"* [{link_label}]({link})\n")
                output.append("\n")
            os.makedirs(os.path.dirname(change_list_file) or ".", exist_ok=True)
            _write_text(change_list_file, output)

    # MkDocs hooks
    def on_pre_build(self, config):  # type: ignore[override]
        base: Optional[str] = None
        target_dir: Optional[str] = None
        change_list_file: Optional[str] = None
        unified: int = 0
        if hasattr(self, "config") and isinstance(self.config, dict):
            base = self.config.get("base")
            target_dir = self.config.get("dir")
            change_list_file = self.config.get("change_list_file")
            if self.config.get("unified") is not None:
                try:
                    unified = int(self.config.get("unified"))
                except Exception:
                    unified = 0

        if not base:
            return

        try:
            self._annotate_before_build(base, target_dir, change_list_file, unified)
        except Exception:
            # Do not fail the build; proceed silently
            self._backups.clear()

    def on_post_build(self, config):  # type: ignore[override]
        # Restore original files
        for fs_path, original_lines in self._backups.items():
            try:
                _write_text(fs_path, original_lines)
            except Exception:
                # Ignore restore failures
                pass
        self._backups.clear()
        return
