#!/usr/bin/env python3
"""
lark.py — 飞书出口（创建飞书云文档 + 可选群通知）

设计原则：长文沉淀物（整理过的课程/视频书）应该落成飞书文档，不是聊天消息。
消息是瞬时的、会被刷掉；文档是持久的、可共享、可检索、可评论。

流程：
1. 用 lark-cli 通过 bot 身份创建一篇飞书 docx
2. 拿到 doc_url
3. 可选：向指定群发送"新文档已整理 → <链接>"的简短通知

前置依赖：
1. 安装 lark-cli: https://github.com/larksuite/oapi-cli-node
2. 创建飞书自建应用，获得 app_id / app_secret
3. 开通权限：docs:document:write, im:message:send_as_bot（如果要发群通知）
4. 如果要发群通知，把 bot 拉进目标群，拿到 chat_id

接口：
    write(title, content, metadata=None, **options) -> str
    返回：创建的飞书文档 URL
"""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def write(title: str, content: str, metadata: Optional[dict] = None, **options) -> str:
    """
    在飞书创建云文档（docx），可选在群里发通知。

    options（必填）:
        - app_id: 飞书 bot App ID
        - app_secret: 飞书 bot App Secret

    options（可选）:
        - chat_id: 群 chat_id (oc_xxxx)。配了就顺手在群里发"新文档已整理"的通知
        - folder_token: 目标文件夹 token（默认创建到 bot 的根目录）
        - wiki_space: wiki 空间 ID（如果想创建到 wiki 里而非普通云文档）
        - wiki_node: wiki 节点 token
        - notify_prefix: 通知消息前缀（默认 "📄 新文档已整理"）

    返回：创建的飞书文档 URL (https://www.feishu.cn/docx/XXX)
    """
    app_id = options["app_id"]
    app_secret = options["app_secret"]

    # 1. lark-cli config 切换到该 bot
    cfg_result = subprocess.run(
        ["lark-cli", "config", "init",
         "--app-id", app_id,
         "--app-secret-stdin",
         "--brand", "feishu"],
        input=app_secret,
        capture_output=True,
        text=True,
    )
    if cfg_result.returncode != 0:
        raise RuntimeError(f"lark-cli config init 失败: {cfg_result.stderr}")

    # 2. 组装完整 markdown 正文（加 metadata 表头）
    body_parts = []
    if metadata:
        meta_lines = []
        for k, v in metadata.items():
            if isinstance(v, list):
                v = " / ".join(str(i) for i in v)
            meta_lines.append(f"- **{k}**: {v}")
        body_parts.append("\n".join(meta_lines))
        body_parts.append("\n---\n")
    body_parts.append(content)
    full_markdown = "\n".join(body_parts)

    # 3. 创建文档（用 bot 身份）
    create_cmd = [
        "lark-cli", "docs", "+create",
        "--as", "bot",
        "--title", title,
        "--markdown", full_markdown,
    ]
    if options.get("folder_token"):
        create_cmd.extend(["--folder-token", options["folder_token"]])
    if options.get("wiki_space"):
        create_cmd.extend(["--wiki-space", options["wiki_space"]])
    if options.get("wiki_node"):
        create_cmd.extend(["--wiki-node", options["wiki_node"]])

    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"飞书文档创建失败：\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"无法解析 lark-cli 输出: {result.stdout}")

    if not payload.get("ok"):
        raise RuntimeError(f"飞书文档创建失败: {payload}")

    doc_url = payload["data"]["doc_url"]
    doc_id = payload["data"]["doc_id"]

    # 4. 可选：给群发通知
    chat_id = options.get("chat_id")
    if chat_id:
        notify_prefix = options.get("notify_prefix", "📄 新文档已整理")
        notification = f"{notify_prefix}\n\n**{title}**\n\n{doc_url}"
        if metadata and metadata.get("原链接"):
            notification += f"\n\n原链接：{metadata['原链接']}"

        notify_cmd = [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--chat-id", chat_id,
            "--text", notification,
        ]
        notify_result = subprocess.run(notify_cmd, capture_output=True, text=True)
        if notify_result.returncode != 0:
            # 通知失败不影响主流程（文档已创建成功），只打印警告
            print(f"⚠️  群通知发送失败（文档已创建）: {notify_result.stderr}")

    return doc_url
