#!/usr/bin/env python3
"""
srt2md.py — .srt 字幕 → 粗 markdown（剥时间戳 + 合并行）

Usage:
    python core/srt2md.py --input <DIR_OR_FILE> --out <DIR>

这一步是机械转换，不做任何语义加工。
后续的"重排为书"由 AI 做（见 prompts/ 和 SKILL.md）。
"""
import argparse
import re
from pathlib import Path


SRT_TIMESTAMP = re.compile(r"^\d{2}:\d{2}:\d{2}[,.]\d+\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d+.*$")
SRT_INDEX = re.compile(r"^\d+\s*$")


def srt_to_text(srt_path: Path) -> str:
    lines = srt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if SRT_INDEX.match(line):
            continue
        if SRT_TIMESTAMP.match(line):
            continue
        # 移除 BOM 和常见字幕样式标签
        line = line.replace("\ufeff", "")
        line = re.sub(r"</?[^>]+>", "", line)
        text_lines.append(line)

    # 相邻去重（AI 字幕常有重复滚动行）
    dedup = []
    prev = None
    for line in text_lines:
        if line != prev:
            dedup.append(line)
        prev = line
    return "\n".join(dedup)


def convert_file(src: Path, out_dir: Path) -> Path:
    text = srt_to_text(src)
    # 文件名: 去掉 .srt 扩展和语言后缀
    stem = src.stem
    for suffix in [".ai-zh", ".zh-CN", ".zh-Hans", ".en", ".zh"]:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    out_path = out_dir / f"{stem}.md"
    out_path.write_text(f"# {stem}\n\n> 原始字幕机械转换（未经 AI 加工）\n\n---\n\n{text}\n", encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="srt 文件或目录")
    parser.add_argument("--out", required=True, help="输出目录")
    args = parser.parse_args()

    src = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if src.is_file():
        files = [src]
    else:
        files = sorted(src.glob("*.srt"))

    if not files:
        print(f"❌ 未找到 .srt 文件: {src}")
        return

    for f in files:
        out = convert_file(f, out_dir)
        print(f"✅ {f.name} → {out.name}")

    print(f"\n共处理 {len(files)} 个字幕，输出到 {out_dir}")


if __name__ == "__main__":
    main()
