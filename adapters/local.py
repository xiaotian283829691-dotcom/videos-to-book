#!/usr/bin/env python3
"""
local.py — 默认出口：写入本地目录

所有 adapter 遵循统一接口：
    write(title: str, content: str, metadata: dict, **options) -> str
    返回：最终写入的路径/URL
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional


def slugify(text: str) -> str:
    """把标题变成文件名安全的 slug"""
    text = re.sub(r"[\\/:*?\"<>|]", "-", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:120]


def write(title: str, content: str, metadata: Optional[dict] = None, **options) -> str:
    """
    写入本地 markdown 文件。

    参数：
        title: 文章标题（会作为文件名）
        content: 完整 markdown 正文
        metadata: 可选元数据（会作为 frontmatter 注入）
        options:
            - dir: 输出目录（默认 ./output）
            - prefix: 文件名前缀（如 "001-"）

    返回：写入的文件绝对路径（str）
    """
    out_dir = Path(options.get("dir", "./output")).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prefix = options.get("prefix", "")
    filename = f"{prefix}{slugify(title)}.md"
    out_path = out_dir / filename

    # 注入 frontmatter（如果有 metadata）
    body = content
    if metadata:
        fm_lines = ["---"]
        for k, v in metadata.items():
            fm_lines.append(f"{k}: {v}")
        fm_lines.append("---")
        body = "\n".join(fm_lines) + "\n\n" + content

    out_path.write_text(body, encoding="utf-8")
    return str(out_path)
