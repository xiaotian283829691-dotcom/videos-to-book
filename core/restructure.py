#!/usr/bin/env python3
"""
restructure.py — AI 重排编排器（可选）

两种使用方式：

1. **交互式（推荐给个人用户）**：
   不用这个脚本，直接在 Claude Code 里调 SKILL：
       claude
       > 用 videos-to-book skill，把 ./tmp/x 里的 srt 按 zh-lecture 规则重排

2. **编程式（适合批量 / cron）**：
   调 Anthropic API 直接跑，不需要 Claude Code 在场：
       python core/restructure.py --input ./tmp/x --prompt zh-lecture-to-book --out ./output

   前置：
       pip install anthropic
       export ANTHROPIC_API_KEY=sk-ant-xxx
       # 或配 cc-company 网关：
       export ANTHROPIC_BASE_URL=https://...
       export ANTHROPIC_AUTH_TOKEN=...
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """加载 prompt 模板（name 可带或不带 .md 后缀）"""
    if not name.endswith(".md"):
        name = f"{name}.md"
    p = PROMPT_DIR / name
    if not p.exists():
        available = [f.stem for f in PROMPT_DIR.glob("*.md")]
        sys.exit(f"❌ 未找到 prompt: {name}。可用：{available}")
    return p.read_text(encoding="utf-8")


def restructure_one(client: "Anthropic", raw_md: str, prompt_template: str,
                    model: str = "claude-opus-4-6") -> str:
    """用 prompt_template 重排单个 md 文件内容"""
    system = prompt_template
    user = f"请按上述规则重排下面的字幕内容：\n\n```\n{raw_md}\n```"

    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="粗 md 目录或单个文件")
    parser.add_argument("--prompt", required=True,
                        help="prompt 名：zh-lecture-to-book / en-to-zh-book / creator-weekly")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--model", default="claude-opus-4-6")
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 个文件（调试用）")
    args = parser.parse_args()

    if Anthropic is None:
        sys.exit("❌ 需要先 `pip install anthropic`")

    client = Anthropic()
    prompt = load_prompt(args.prompt)

    src = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [src] if src.is_file() else sorted(src.glob("*.md"))
    if args.limit:
        files = files[:args.limit]

    if not files:
        sys.exit(f"❌ 未找到 md 文件: {src}")

    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 重排: {f.name}")
        raw = f.read_text(encoding="utf-8")
        try:
            structured = restructure_one(client, raw, prompt, model=args.model)
            out_path = out_dir / f.name
            out_path.write_text(structured, encoding="utf-8")
            print(f"  ✅ → {out_path}")
        except Exception as e:
            print(f"  ❌ {e}")

    print(f"\n完成，{len(files)} 个文件已输出到 {out_dir}")


if __name__ == "__main__":
    main()
