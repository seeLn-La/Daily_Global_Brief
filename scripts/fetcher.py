"""RSS 新闻抓取模块：从配置的 RSS 源拉取文章，去重并过滤。"""
import concurrent.futures
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional

import feedparser
import requests

from config import DATA_DIR, FEED_TIMEOUT, RSS_SOURCES

# 抓取最近多少小时内的文章（24h = 覆盖完整上一个新闻周期）
LOOKBACK_HOURS = 24

# 并发抓取线程数
MAX_FETCH_WORKERS = 8

# 连续失败达到阈值后，临时跳过该源
FAILURE_SKIP_THRESHOLD = 3

# 跳过窗口：最近多久内连续失败的源会被暂时跳过
SKIP_WINDOW_HOURS = 48

USER_AGENT = "Mozilla/5.0 (compatible; NewsBot/1.0)"

# RSS 源偶尔会把站点错误页当成文章返回。此类标题不应进入新闻池。
ERROR_TITLE_MARKERS = (
    "error 500",
    "that's an error",
    "there was an error",
    "please try again later",
)


def _health_file_path() -> str:
    """返回源健康记录文件路径。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(script_dir), DATA_DIR)
    os.makedirs(data_path, exist_ok=True)
    return os.path.join(data_path, "source_health.json")


def _load_health_state() -> dict:
    """读取源健康记录。"""
    path = _health_file_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError):
        return {}


def _save_health_state(state: dict) -> None:
    """保存源健康记录。"""
    path = _health_file_path()
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    """解析 ISO 时间字符串。"""
    try:
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _should_skip_source(url: str, health_state: dict, now: datetime) -> bool:
    """判断源是否因连续失败而需要临时跳过。"""
    record = health_state.get(url, {})
    failures = int(record.get("consecutive_failures", 0) or 0)
    if failures < FAILURE_SKIP_THRESHOLD:
        return False

    last_failure_at = _parse_iso_datetime(record.get("last_failure_at", ""))
    if last_failure_at is None:
        return True

    age_hours = (now - last_failure_at).total_seconds() / 3600
    return age_hours < SKIP_WINDOW_HOURS


@dataclass
class Article:
    """单篇新闻文章"""
    title: str
    url: str
    source: str
    category: str
    published: Optional[datetime] = None
    summary: str = ""

    def url_hash(self) -> str:
        """生成 URL 哈希用于去重"""
        return hashlib.md5(self.url.encode()).hexdigest()


def _clean_title(raw_title: str) -> str:
    """清洗标题：去除 HTML 标签、多余空白、常见噪音前缀。"""
    # 去除 HTML 标签
    text = re.sub(r"<[^>]+>", "", raw_title)
    # 解码 HTML 实体
    text = unescape(text)
    # 去除常见噪音前缀
    text = re.sub(r"^(BREAKING|EXCLUSIVE|UPDATED|UPDATE|JUST IN)\s*[:：\-—]+\s*", "", text, flags=re.IGNORECASE)
    # 合并多余空白
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_error_page_title(title: str) -> bool:
    """识别 RSS 将站点错误页误报为文章的情况。"""
    normalized = re.sub(r"\s+", " ", unescape(title)).strip().lower()
    return sum(marker in normalized for marker in ERROR_TITLE_MARKERS) >= 3


def _parse_date(entry) -> Optional[datetime]:
    """从 RSS entry 中解析发布时间，返回 UTC datetime 或 None。"""
    raw = entry.get("published") or entry.get("updated") or entry.get("created")
    if raw:
        if isinstance(raw, datetime):
            parsed = raw
        else:
            parsed = None
            raw_text = str(raw).strip()
            try:
                parsed = parsedate_to_datetime(raw_text)
            except (TypeError, ValueError, IndexError):
                # feedparser 常见的 ISO 8601 格式（例如 2026-06-16T16:00:00Z）
                try:
                    parsed = datetime.fromisoformat(raw_text.replace("Z", "+00:00"))
                except ValueError:
                    parsed = None
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    # 某些 RSS 只提供 feedparser 转换后的 *_parsed 字段。
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(key)
        if not parsed:
            continue
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


def _extract_source(feed: dict, entry: dict) -> str:
    """提取来源名称：优先用 RSS 标题，其次从 URL 推断。"""
    feed_title = feed.get("feed", {}).get("title", "")
    if feed_title:
        return feed_title
    # 降级：从 entry link 提取域名
    link = entry.get("link", "")
    match = re.search(r"https?://(?:www\.)?([^/]+)", link)
    return match.group(1) if match else "Unknown"


def _is_recent(published: Optional[datetime], cutoff: datetime) -> bool:
    """判断文章是否在时间窗口内。无日期信息的文章默认保留。"""
    if published is None:
        return True
    return published >= cutoff


def _fetch_one(url: str, category: str, cutoff: datetime) -> tuple[str, str, list[Article], Optional[str]]:
    """抓取单个 RSS 源，返回文章列表。异常时返回空列表。"""
    try:
        resp = requests.get(url, timeout=FEED_TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"[WARN] 抓取失败: {url} — {e}", file=sys.stderr)
        return url, category, [], str(e)

    if feed.bozo and not feed.entries:
        print(f"[WARN] RSS 解析异常: {url}", file=sys.stderr)
        return url, category, [], "rss_parse_error"

    articles = []
    for entry in feed.entries:
        title = _clean_title(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
            continue
        if _is_error_page_title(title):
            print(f"[WARN] 跳过错误页条目: {url} — {title[:80]}", file=sys.stderr)
            continue

        published = _parse_date(entry)
        if not _is_recent(published, cutoff):
            continue

        source = _extract_source(feed, entry)
        article = Article(
            title=title,
            url=link,
            source=source,
            category=category,
            published=published,
            summary=title,  # 初始摘要 = 清洗后的标题
        )
        articles.append(article)

    print(f"[OK] {url} → {len(articles)} 篇")
    return url, category, articles, None


def fetch_all() -> list[Article]:
    """抓取所有 RSS 源，去重并返回文章列表。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    print(f"时间窗口: {cutoff.strftime('%Y-%m-%d %H:%M UTC')} ~ 现在\n")

    now = datetime.now(timezone.utc)
    health_state = _load_health_state()
    active_urls = {src["url"] for src in RSS_SOURCES}
    pruned_health_state = {url: record for url, record in health_state.items() if url in active_urls}
    if len(pruned_health_state) != len(health_state):
        removed = len(health_state) - len(pruned_health_state)
        print(f"[INFO] 清理 {removed} 条过期源健康记录")
    health_state = pruned_health_state
    all_articles: list[Article] = []
    seen_urls: set[str] = set()
    results: list[tuple[str, str, list[Article], Optional[str]]] = []

    active_sources = []
    skipped_sources = []
    for src in RSS_SOURCES:
        if _should_skip_source(src["url"], health_state, now):
            skipped_sources.append(src["url"])
            continue
        active_sources.append(src)

    if skipped_sources:
        print(f"[INFO] 因连续失败暂时跳过 {len(skipped_sources)} 个源")

    if active_sources:
        max_workers = min(MAX_FETCH_WORKERS, len(active_sources))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_fetch_one, src["url"], src["category"], cutoff): src
                for src in active_sources
            }
            for future in concurrent.futures.as_completed(future_map):
                try:
                    results.append(future.result())
                except Exception as e:  # noqa: BLE001
                    src = future_map[future]
                    print(f"[WARN] 抓取任务异常: {src['url']} — {e}", file=sys.stderr)
                    results.append((src["url"], src["category"], [], str(e)))

    # 按原始配置顺序回收文章，保证日志更稳定
    result_map = {url: (url, category, articles, error) for url, category, articles, error in results}
    for src in active_sources:
        url = src["url"]
        if url not in result_map:
            continue
        _, _, articles, error = result_map[url]
        record = health_state.get(url, {})
        if error is None:
            health_state[url] = {
                "url": url,
                "category": src["category"],
                "last_status": "ok",
                "last_success_at": now.isoformat(),
                "last_failure_at": record.get("last_failure_at"),
                "consecutive_failures": 0,
                "last_error": None,
            }
        else:
            consecutive_failures = int(record.get("consecutive_failures", 0) or 0) + 1
            health_state[url] = {
                "url": url,
                "category": src["category"],
                "last_status": "fail",
                "last_success_at": record.get("last_success_at"),
                "last_failure_at": now.isoformat(),
                "consecutive_failures": consecutive_failures,
                "last_error": error,
            }

        for a in articles:
            h = a.url_hash()
            if h not in seen_urls:
                seen_urls.add(h)
                all_articles.append(a)

    # 跳过的源不增加失败计数，只保留最近一次状态
    for url in skipped_sources:
        record = health_state.get(url, {})
        health_state[url] = {
            "url": url,
            "category": record.get("category"),
            "last_status": "skipped_health",
            "last_success_at": record.get("last_success_at"),
            "last_failure_at": record.get("last_failure_at"),
            "consecutive_failures": int(record.get("consecutive_failures", 0) or 0),
            "last_error": record.get("last_error"),
        }

    _save_health_state(health_state)
    print(f"\n总计: {len(all_articles)} 篇 (去重后)")
    return all_articles
