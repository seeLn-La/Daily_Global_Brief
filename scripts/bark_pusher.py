"""Bark 推送模块：将每日新闻摘要推送到 iPhone。"""
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

import requests

from config import DATA_DIR


def _read_today_json() -> dict | None:
    """读取今日新闻 JSON 文件。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = os.path.join(os.path.dirname(script_dir), DATA_DIR, f"{date_str}.json")

    if not os.path.exists(json_path):
        print(f"[WARN] 数据文件不存在: {json_path}", file=sys.stderr)
        return None

    with open(json_path, "r") as f:
        return json.load(f)


def _build_message(data: dict, pages_url: str) -> tuple[str, str] | None:
    """构建推送标题和正文。如果三个分类均为空，返回 None（不推送）。"""
    counts = {}
    for cat_key in ["technology", "business", "ai"]:
        cat_data = data.get("categories", {}).get(cat_key, {})
        counts[cat_key] = len(cat_data.get("articles", []))

    total = sum(counts.values())
    if total == 0:
        return None

    title = f"{data['date']} 新闻速递"

    name_map = {"technology": "科技", "business": "商业", "ai": "AI"}
    parts = []
    for cat_key, label in name_map.items():
        parts.append(f"{label} {counts[cat_key]} 篇")
    body = f"{', '.join(parts)} 共 {total} 篇 — 点击查看 {pages_url}"

    return title, body


def send_notification(pages_url: str | None = None):
    """发送 Bark 推送通知。"""
    device_key = os.environ.get("BARK_DEVICE_KEY", "")
    if not device_key:
        print("[SKIP] 未设置 BARK_DEVICE_KEY 环境变量，跳过推送")
        return

    if not pages_url:
        pages_url = os.environ.get("PAGES_URL", "https://github.com")

    data = _read_today_json()
    if data is None:
        print("[SKIP] 无数据文件，跳过推送")
        return

    msg = _build_message(data, pages_url)
    if msg is None:
        print("[SKIP] 所有分类均无文章，跳过推送")
        return

    title, body = msg
    encoded_title = urllib.parse.quote(title)
    encoded_body = urllib.parse.quote(body)
    url = f"https://api.day.app/{device_key}/{encoded_title}/{encoded_body}"

    try:
        resp = requests.post(url, timeout=10)
        result = resp.json()
        print(f"[Bark] 推送结果: {result}")
    except Exception as e:
        print(f"[WARN] Bark 推送失败: {e}", file=sys.stderr)


if __name__ == "__main__":
    send_notification()
