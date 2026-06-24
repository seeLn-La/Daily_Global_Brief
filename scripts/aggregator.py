"""主编排脚本：抓取 → 分类 → 排序 → 翻译 → 写入 JSON。"""
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from config import (
    CATEGORY_NAMES,
    DATA_DIR,
    MAX_ARTICLES_PER_CATEGORY,
    MAX_CANDIDATES_PER_CATEGORY,
    MAX_CANDIDATES_PER_SOURCE,
)
from fetcher import Article, fetch_all
from translator import translate_articles

CATEGORY_KEYWORDS = {
    "technology": [
        "tech",
        "technology",
        "software",
        "hardware",
        "chip",
        "chips",
        "semiconductor",
        "gpu",
        "cpu",
        "ai",
        "cloud",
        "security",
        "platform",
        "device",
        "startup",
        "open source",
        "robot",
        "mobile",
        "android",
        "ios",
        "windows",
        "linux",
        "苹果",
        "芯片",
        "硬件",
        "软件",
        "平台",
        "云",
        "安全",
        "设备",
        "终端",
        "系统",
    ],
    "business": [
        "business",
        "market",
        "markets",
        "stock",
        "stocks",
        "earnings",
        "revenue",
        "profit",
        "loss",
        "economy",
        "economic",
        "inflation",
        "rates",
        "fed",
        "bank",
        "deal",
        "merger",
        "acquisition",
        "ipo",
        "investment",
        "investor",
        "ceo",
        "trading",
        "tariff",
        "finance",
        "财报",
        "营收",
        "利润",
        "亏损",
        "市场",
        "股",
        "并购",
        "融资",
        "投资",
        "经济",
        "通胀",
        "利率",
        "企业",
    ],
    "ai": [
        "ai",
        "artificial intelligence",
        "llm",
        "agent",
        "agents",
        "model",
        "models",
        "training",
        "inference",
        "fine-tuning",
        "foundation model",
        "multimodal",
        "prompt",
        "rag",
        "token",
        "transformer",
        "machine learning",
        "deep learning",
        "openai",
        "anthropic",
        "gpt",
        "claude",
        "gemini",
        "copilot",
        "智能体",
        "大模型",
        "模型",
        "训练",
        "推理",
        "生成式",
        "人工智能",
        "算力",
        "向量",
        "语义",
    ],
}

SOURCE_BONUS = {
    "technology": [
        "TechCrunch",
        "The Verge",
        "Ars Technica",
        "WIRED",
        "MIT Technology Review",
        "Hacker News",
        "Engadget",
        "极客公园",
        "36氪",
        "爱范儿",
        "钛媒体",
    ],
    "business": [
        "CNBC",
        "BBC News",
        "MarketWatch",
        "The Economist",
        "Business Insider",
        "Reuters",
        "Bloomberg",
        "NYT",
    ],
    "ai": [
        "OpenAI",
        "NVIDIA",
        "MIT Technology Review",
        "TechCrunch",
        "VentureBeat",
        "The Decoder",
        "Synced",
        "AI News",
        "MarkTechPost",
        "KDnuggets",
        "量子位",
        "机器之心",
        "智东西",
        "aibusiness",
        "TechXplore",
    ],
}

MIN_CANDIDATE_SCORE = {
    "technology": 2,
    "business": 2,
    "ai": 2,
}

MIN_FINAL_SCORE = {
    "technology": 3,
    "business": 3,
    "ai": 3,
}

STRONG_MATCH_SCORE = {
    "technology": 5,
    "business": 5,
    "ai": 5,
}

ENGLISH_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "that",
    "the",
    "this",
    "to",
    "with",
}

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def _ensure_data_dir() -> str:
    """确保数据目录存在，返回绝对路径。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(script_dir), DATA_DIR)
    os.makedirs(data_path, exist_ok=True)
    return data_path


def _sort_articles(articles: list[Article]) -> list[Article]:
    """按发布时间倒序，未标注时间的文章排在后面。"""
    dated = [a for a in articles if a.published is not None]
    undated = [a for a in articles if a.published is None]
    dated.sort(key=lambda a: a.published, reverse=True)
    return dated + undated


def _article_score(article: Article, category: str) -> float:
    """根据标题主题、来源可信度和时效性给文章打分。"""
    text = f"{article.summary} {article.source}".lower()
    score = 0.0

    for keyword in CATEGORY_KEYWORDS.get(category, []):
        if keyword.lower() in text:
            score += 1.0

    source_text = article.source.lower()
    for source_name in SOURCE_BONUS.get(category, []):
        if source_name.lower() in source_text:
            score += 1.5
            break

    if article.published is not None:
        now = datetime.now(timezone.utc)
        age_hours = max((now - article.published).total_seconds() / 3600, 0)
        score += max(0.0, 6.0 - age_hours / 4.0)

    return score


def _rank_articles(articles: list[Article], category: str) -> list[Article]:
    """按相关性和时效性排序，相关性更高的排前面。"""
    return sorted(
        articles,
        key=lambda article: (
            _article_score(article, category),
            article.published or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )


def _normalize_url(url: str) -> str:
    """移除常见跟踪参数，识别指向同一文章的 URL。"""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def _normalize_title(title: str) -> str:
    """统一标题格式，便于精确比较和相似度计算。"""
    text = unicodedata.normalize("NFKC", title).lower()
    text = re.sub(
        r"^(breaking|exclusive|updated|update|just in)\s*[:：\-—]+\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _meaningful_tokens(normalized_title: str) -> set[str]:
    """提取英文标题中的有效词语，过滤常见虚词。"""
    return {
        token
        for token in normalized_title.split()
        if len(token) > 1 and token not in ENGLISH_STOPWORDS
    }


def _is_same_event(first: Article, second: Article) -> bool:
    """使用保守阈值判断两篇文章是否在报道同一事件。"""
    first_title = _normalize_title(first.summary)
    second_title = _normalize_title(second.summary)
    if not first_title or not second_title:
        return False
    if first_title == second_title:
        return True

    compact_first = first_title.replace(" ", "")
    compact_second = second_title.replace(" ", "")
    if min(len(compact_first), len(compact_second)) < 12:
        return False

    character_similarity = SequenceMatcher(None, first_title, second_title).ratio()
    if character_similarity >= 0.88:
        return True

    first_tokens = _meaningful_tokens(first_title)
    second_tokens = _meaningful_tokens(second_title)
    common_count = len(first_tokens & second_tokens)
    if common_count < 4:
        return False

    union_count = len(first_tokens | second_tokens)
    smaller_count = min(len(first_tokens), len(second_tokens))
    token_overlap = common_count / smaller_count if smaller_count else 0.0
    token_jaccard = common_count / union_count if union_count else 0.0
    return token_overlap >= 0.65 and token_jaccard >= 0.40 and character_similarity >= 0.45


def _find_duplicate_event(article: Article, selected: list[dict]) -> Article | None:
    """返回已选列表中的同事件文章；没有重复时返回 None。"""
    for item in selected:
        existing = item["article"]
        if _normalize_url(article.url) == _normalize_url(existing.url):
            return existing
        if _is_same_event(article, existing):
            return existing
    return None


def _select_candidates(cat_articles: list[Article], category: str) -> list[Article]:
    """为单个分类生成候选池。

    候选池优先保证时效性，同时限制单一来源最多保留少量文章，
    避免一个站点把整个板块占满。
    """
    ranked = _rank_articles(cat_articles, category)
    source_counts: dict[str, int] = defaultdict(int)
    candidates: list[Article] = []
    fallback: list[Article] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    duplicate_count = 0

    def add_candidate(article: Article) -> bool:
        """加入候选池；URL 或标题完全重复时跳过。"""
        nonlocal duplicate_count
        normalized_url = _normalize_url(article.url)
        normalized_title = _normalize_title(article.summary)
        if normalized_url in seen_urls or normalized_title in seen_titles:
            duplicate_count += 1
            print(f"  [去重/候选] {article.source}: {article.summary}")
            return False
        candidates.append(article)
        source_counts[article.source] += 1
        seen_urls.add(normalized_url)
        seen_titles.add(normalized_title)
        return True

    for article in ranked:
        if _article_score(article, category) < MIN_CANDIDATE_SCORE[category]:
            fallback.append(article)
            continue
        if source_counts[article.source] >= MAX_CANDIDATES_PER_SOURCE:
            continue
        add_candidate(article)
        if len(candidates) >= MAX_CANDIDATES_PER_CATEGORY:
            break

    if len(candidates) < MAX_CANDIDATES_PER_CATEGORY:
        for article in fallback:
            if source_counts[article.source] >= MAX_CANDIDATES_PER_SOURCE:
                continue
            add_candidate(article)
            if len(candidates) >= MAX_CANDIDATES_PER_CATEGORY:
                break

    if duplicate_count:
        print(f"  [去重/候选] {category} 共跳过 {duplicate_count} 篇完全重复文章")

    return candidates


def _select_final_articles(candidates: list[Article], category: str) -> list[dict]:
    """从候选池中挑出最终展示的文章。

    先尽量保证来源多样性；如果还不够，再按顺序补齐。
    返回值包含文章对象和入选原因，方便后续写入 JSON。
    """
    selected: list[dict] = []
    seen_sources: set[str] = set()
    reported_duplicates: set[str] = set()
    ranked = _rank_articles(candidates, category)

    def is_duplicate(article: Article) -> bool:
        """检查最终列表中的同事件文章，并保证每篇只记录一次日志。"""
        existing = _find_duplicate_event(article, selected)
        if existing is None:
            return False
        duplicate_key = _normalize_url(article.url)
        if duplicate_key not in reported_duplicates:
            reported_duplicates.add(duplicate_key)
            print(
                f"  [去重/最终] {article.source}: {article.summary} "
                f"→ 保留 {existing.source}: {existing.summary}"
            )
        return True

    for article in ranked:
        score = _article_score(article, category)
        if score < STRONG_MATCH_SCORE[category]:
            continue
        if article.source in seen_sources:
            continue
        if is_duplicate(article):
            continue
        selected.append(
            {
                "article": article,
                "selection_tier": "strong_match",
                "selection_reason": "高相关且来源优先",
                "selection_score": round(score, 2),
            }
        )
        seen_sources.add(article.source)
        if len(selected) >= MAX_ARTICLES_PER_CATEGORY:
            return selected

    for article in ranked:
        score = _article_score(article, category)
        if score < MIN_FINAL_SCORE[category]:
            continue
        if any(item["article"] is article for item in selected):
            continue
        if is_duplicate(article):
            continue
        selected.append(
            {
                "article": article,
                "selection_tier": "soft_match",
                "selection_reason": "主题相关，补足数量",
                "selection_score": round(score, 2),
            }
        )
        seen_sources.add(article.source)
        if len(selected) >= MAX_ARTICLES_PER_CATEGORY:
            break

    if len(selected) < MAX_ARTICLES_PER_CATEGORY:
        for article in ranked:
            if any(item["article"] is article for item in selected):
                continue
            if is_duplicate(article):
                continue
            selected.append(
                {
                    "article": article,
                    "selection_tier": "fill",
                    "selection_reason": "数量补位",
                    "selection_score": round(_article_score(article, category), 2),
                }
            )
            if len(selected) >= MAX_ARTICLES_PER_CATEGORY:
                break

    if reported_duplicates:
        print(f"  [去重/最终] {category} 共跳过 {len(reported_duplicates)} 篇同事件文章")

    return selected


def _group_by_category(articles: list[Article]) -> dict:
    """按分类分组文章，输出候选池和最终展示列表。"""
    groups = defaultdict(list)
    for a in articles:
        groups[a.category].append(a)

    result = {}
    for category in CATEGORY_NAMES:
        cat_articles = groups.get(category, [])
        candidates = _select_candidates(cat_articles, category)
        final_articles = _select_final_articles(candidates, category)
        result[category] = {
            "candidates": candidates,
            "articles": final_articles,
        }

    return result


def _build_json_data(date_str: str, categorized: dict) -> dict:
    """构建输出 JSON 数据结构。"""
    categories_json = {}
    for cat_key, cat_names in CATEGORY_NAMES.items():
        category_data = categorized.get(cat_key, {})
        articles = category_data.get("articles", [])
        candidates = category_data.get("candidates", [])
        categories_json[cat_key] = {
            "name_zh": cat_names["zh"],
            "name_en": cat_names["en"],
            "articles": [
                {
                    "summary_zh": getattr(item["article"], "summary_zh", item["article"].summary),
                    "summary_en": getattr(item["article"], "summary_en", item["article"].summary),
                    "source": item["article"].source,
                    "url": item["article"].url,
                    "published": item["article"].published.isoformat() if item["article"].published else None,
                    "selection_tier": item["selection_tier"],
                    "selection_reason": item["selection_reason"],
                    "selection_score": item["selection_score"],
                }
                for item in articles
            ],
            "candidates": [
                {
                    "summary": a.summary,
                    "source": a.source,
                    "url": a.url,
                    "published": a.published.isoformat() if a.published else None,
                }
                for a in candidates
            ],
        }

    return {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "categories": categories_json,
    }


def _update_index(data_dir: str, date_str: str) -> list:
    """更新日期索引文件，返回完整的日期列表。"""
    index_path = os.path.join(data_dir, "index.json")
    dates: list[str] = []

    if os.path.exists(index_path):
        try:
            with open(index_path, "r") as f:
                dates = json.load(f)
        except (json.JSONDecodeError, IOError):
            dates = []

    if date_str not in dates:
        dates.append(date_str)
        dates.sort()

    with open(index_path, "w") as f:
        json.dump(dates, f, ensure_ascii=False, indent=2)

    return dates


def _write_push_message(data_dir: str, json_data: dict):
    """输出推送 URL 路径文件，供 iOS Shortcuts 读取（一行文本，零解析）。"""
    from urllib.parse import quote

    counts = {}
    for cat_key in ["technology", "business", "ai"]:
        cat_data = json_data.get("categories", {}).get(cat_key, {})
        counts[cat_key] = len(cat_data.get("articles", []))

    total = sum(counts.values())
    name_map = {"technology": "科技", "business": "商业", "ai": "AI"}
    parts = [f"{name_map[k]} {v} 篇" for k, v in counts.items()]
    body = f"{', '.join(parts)}，共 {total} 篇"

    title = f"{json_data['date']} 新闻速递"
    url = "https://seeln-la.github.io/news"

    # 预编码 URL 路径，Shortcuts 直接拼接即可
    path = f"/{quote(title, safe='')}/{quote(body, safe='')}?url={quote(url, safe='')}"
    filepath = os.path.join(data_dir, "push_url.txt")
    with open(filepath, "w") as f:
        f.write(path)
    print(f"推送 URL 路径文件: {filepath}")


def main():
    """入口：执行完整新闻聚合流程。"""
    print("=" * 50)
    print("Daily News Aggregation")
    print("=" * 50)

    # 1. 抓取
    articles = fetch_all()
    if not articles:
        print("[INFO] 未抓取到任何文章，生成空数据文件")

    # 2. 分类 + 排序 + Top N
    categorized = _group_by_category(articles)
    for cat_key, cat_articles in categorized.items():
        name = CATEGORY_NAMES[cat_key]["zh"]
        candidate_count = len(cat_articles.get("candidates", []))
        final_count = len(cat_articles.get("articles", []))
        print(f"  {name}: 候选 {candidate_count} 篇，最终 {final_count} 篇")

    # 3. 翻译
    all_selected = []
    for cat_data in categorized.values():
        for item in cat_data.get("articles", []):
            all_selected.append(item["article"])
    translate_articles(all_selected)

    # 4. 写入 JSON
    data_dir = _ensure_data_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_data = _build_json_data(today, categorized)

    json_path = os.path.join(data_dir, f"{today}.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 5. 生成简化推送消息文件（供 iOS Shortcuts 读取）
    _write_push_message(data_dir, json_data)

    # 6. 更新索引
    all_dates = _update_index(data_dir, today)

    print(f"\n数据文件: {json_path}")
    print(f"索引文件: 共 {len(all_dates)} 个日期")
    print("完成!")


if __name__ == "__main__":
    main()
