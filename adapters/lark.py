#!/usr/bin/env python3
"""
lark.py — 飞书出口（通过 lark-cli 发到群）

前置依赖：
1. 安装 lark-cli: https://github.com/larksuite/oapi-cli-node
2. 创建一个飞书 bot，获得 app_id 和 app_secret
3. 把 bot 拉进目标群，拿到 chat_id

接口：
    write(title, content, metadata=None, **options) -> str
    返回：飞书 message_id
"""
import json
import subprocess
import tempfile
from pathlib import Path


def write(title: str, content: str, metadata: dict | None = None, **options) -> str:
    """
    发送到飞书群。

    options（必填）:
        - app_id: 飞书 bot App ID
        - app_secret: 飞书 bot App Secret
        - chat_id: 目标群 chat_id (oc_xxxx)

    options（可选）:
        - msg_type: "text" | "post"（富文本，默认 post）
        - split_threshold: 超过这个字符数自动拆成多条（默认 4000）
    """
    app_id = options["app_id"]
    app_secret = options["app_secret"]
    chat_id = options["chat_id"]
    msg_type = options.get("msg_type", "post")
    split_threshold = options.get("split_threshold", 4000)

    # 1. 切换 lark-cli config 到指定 bot
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

    # 2. 组装完整消息
    header = f"# {title}\n\n"
    if metadata:
        meta_lines = [f"**{k}**: {v}" for k, v in metadata.items()]
        header += " · ".join(meta_lines) + "\n\n---\n\n"
    full_body = header + content

    # 3. 按阈值拆分
    chunks = _split_markdown(full_body, split_threshold)

    message_ids = []
    for i, chunk in enumerate(chunks):
        text_with_marker = chunk if len(chunks) == 1 else f"{chunk}\n\n（{i+1}/{len(chunks)}）"

        send_cmd = [
            "lark-cli", "im", "+messages-send",
            "--as", "bot",
            "--chat-id", chat_id,
            "--text", text_with_marker,
        ]
        result = subprocess.run(send_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"飞书发送失败（第 {i+1}/{len(chunks)} 段）: {result.stderr}")

        # 解析 message_id
        try:
            out = json.loads(result.stdout)
            msg_id = out.get("data", {}).get("message_id", "")
            if msg_id:
                message_ids.append(msg_id)
        except json.JSONDecodeError:
            pass

    return ",".join(message_ids) if message_ids else "sent"


def _split_markdown(text: str, threshold: int) -> list[str]:
    """按段落拆分长 markdown，尽量在自然边界切"""
    if len(text) <= threshold:
        return [text]

    chunks = []
    current = []
    current_len = 0
    for para in text.split("\n\n"):
        para_len = len(para)
        if current_len + para_len > threshold and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len
        else:
            current.append(para)
            current_len += para_len + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks
