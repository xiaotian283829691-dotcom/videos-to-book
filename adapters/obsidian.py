#!/usr/bin/env python3
"""
obsidian.py — Obsidian vault 出口

把重排后的 markdown 写入指定 Obsidian vault 的子目录，
Obsidian 打开后可直接检索/双向链接/图谱。

接口：
    write(title, content, metadata=None, **options) -> str
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional


def slugify(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]", "-", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:120]


def write(title: str, content: str, metadata: Optional[dict] = None, **options) -> str:
    """
    写入 Obsidian vault。

    options:
        - vault_path: Obsidian vault 根路径（默认 ~/Documents/obsidian-vault）
        - subdir: vault 下的子目录（默认 "video-notes"）
        - prefix: 文件名前缀
        - add_backlinks: 是否在尾部加常用 backlinks 区（默认 False）
    """
    vault = Path(options.get("vault_path", "~/Documents/obsidian-vault")).expanduser().resolve()
    if not vault.exists():
        raise FileNotFoundError(f"Obsidian vault 不存在: {vault}")

    subdir = options.get("subdir", "video-notes")
    target_dir = vault / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    prefix = options.get("prefix", "")
    filename = f"{prefix}{slugify(title)}.md"
    out_path = target_dir / filename

    # 构建 frontmatter（Obsidian 识别 YAML frontmatter 做 metadata）
    body_parts = []
    if metadata:
        body_parts.append("---")
        for k, v in metadata.items():
            if isinstance(v, list):
                body_parts.append(f"{k}:")
                for item in v:
                    body_parts.append(f"  - {item}")
            else:
                body_parts.append(f"{k}: {v}")
        body_parts.append("---\n")

    body_parts.append(content)

    if options.get("add_backlinks"):
        body_parts.append("\n\n---\n\n## 相关\n\n- [[video-notes/README]]\n")

    out_path.write_text("\n".join(body_parts), encoding="utf-8")
    return str(out_path)
