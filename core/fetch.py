#!/usr/bin/env python3
"""
fetch.py — yt-dlp 封装，抓字幕 + 元数据

Usage:
    python core/fetch.py --url <URL> [--out <DIR>] [--config <PATH>]

支持：
- 单个视频
- B 站合集 / YouTube 播放列表
- YouTube 频道（自动遍历所有视频）

输出：
    <out>/
    ├── 001-xxx.ai-zh.srt
    ├── 001-xxx.info.json
    ├── 002-xxx.ai-zh.srt
    └── ...
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


DEFAULT_CONFIG = {
    "fetch": {
        "ytdlp_bin": "yt-dlp",
        "cookies_from_browser": "chrome",
        "proxy": "",
        "sub_langs": ["ai-zh", "zh-CN", "en", "zh-Hans"],
    }
}


def load_config(path: str | None) -> dict:
    if not path or not os.path.exists(path) or yaml is None:
        return DEFAULT_CONFIG
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    # Merge with defaults
    merged = DEFAULT_CONFIG.copy()
    if "fetch" in cfg:
        merged["fetch"].update(cfg["fetch"])
    return merged


def build_ytdlp_cmd(url: str, out_dir: Path, fetch_cfg: dict) -> list[str]:
    cmd = [
        fetch_cfg["ytdlp_bin"],
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", ",".join(fetch_cfg["sub_langs"]),
        "--sub-format", "srt/best",
        "--convert-subs", "srt",
        "--write-info-json",
        "--output", str(out_dir / "%(playlist_index|)03d-%(title).200s.%(ext)s"),
    ]
    if fetch_cfg.get("cookies_from_browser"):
        cmd.extend(["--cookies-from-browser", fetch_cfg["cookies_from_browser"]])
    if fetch_cfg.get("proxy"):
        cmd.extend(["--proxy", fetch_cfg["proxy"]])
    cmd.append(url)
    return cmd


def main():
    parser = argparse.ArgumentParser(description="Fetch video subtitles via yt-dlp")
    parser.add_argument("--url", required=True, help="Video / playlist / channel URL")
    parser.add_argument("--out", default="./tmp/fetch", help="Output directory")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    cfg = load_config(args.config)
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_ytdlp_cmd(args.url, out_dir, cfg["fetch"])
    print(f"[fetch] → {out_dir}")
    print(f"[cmd] {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit(f"❌ 找不到 yt-dlp，请先 `pip install yt-dlp`")
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ yt-dlp 抓取失败（exit {e.returncode}）。"
                 f"常见原因：①未登录浏览器 ②节点被封 ③URL 失效")

    srt_count = len(list(out_dir.glob("*.srt")))
    print(f"✅ 抓取完成，{srt_count} 个字幕文件")


if __name__ == "__main__":
    main()
