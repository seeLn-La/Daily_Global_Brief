"""RSS 新闻抓取模块：从配置的 RSS 源拉取文章，去重并过滤。"""
import hashlib
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import requests

from config import FEED_TIMEOUT, RSS_SOURCES

# 抓取最近多少小时内的文章（24h = 覆盖完整上一个新闻周期）
LOOKBACK_HOURS = 24


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
    from html import unescape
    text = unescape(text)
    # 去除常见噪音前缀
    text = re.sub(r"^(BREAKING|EXCLUSIVE|UPDATED|UPDATE|JUST IN)\s*[:：\-—]+\s*", "", text, flags=re.IGNORECASE)
    # 合并多余空白
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date(entry) -> Optional[datetime]:
    """从 RSS entry 中解析发布时间，返回 UTC datetime 或 None。"""
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
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


def _fetch_one(url: str, category: str, cutoff: datetime) -> list[Article]:
    """抓取单个 RSS 源，返回文章列表。异常时返回空列表。"""
    try:
        resp = requests.get(url, timeout=FEED_TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        print(f"[WARN] 抓取失败: {url} — {e}", file=sys.stderr)
        return []

    if feed.bozo and not feed.entries:
        print(f"[WARN] RSS 解析异常: {url}", file=sys.stderr)
        return []

    articles = []
    for entry in feed.entries:
        title = _clean_title(entry.get("title", ""))
        link = entry.get("link", "")
        if not title or not link:
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
    return articles


def fetch_all() -> list[Article]:
    """抓取所有 RSS 源，去重并返回文章列表。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    print(f"时间窗口: {cutoff.strftime('%Y-%m-%d %H:%M UTC')} ~ 现在\n")

    all_articles: list[Article] = []
    seen_urls: set[str] = set()

    for src in RSS_SOURCES:
        articles = _fetch_one(src["url"], src["category"], cutoff)
        for a in articles:
            h = a.url_hash()
            if h not in seen_urls:
                seen_urls.add(h)
                all_articles.append(a)

    print(f"\n总计: {len(all_articles)} 篇 (去重后)")
    return all_articles
