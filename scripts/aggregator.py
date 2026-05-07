"""主编排脚本：抓取 → 分类 → 排序 → 翻译 → 写入 JSON。"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

from config import CATEGORY_NAMES, DATA_DIR, MAX_ARTICLES_PER_CATEGORY
from fetcher import Article, fetch_all
from translator import translate_articles


def _ensure_data_dir() -> str:
    """确保数据目录存在，返回绝对路径。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(os.path.dirname(script_dir), DATA_DIR)
    os.makedirs(data_path, exist_ok=True)
    return data_path


def _group_by_category(articles: list[Article]) -> dict:
    """按分类分组文章。每组按发布时间倒序，每个来源只取一篇，最后取 Top N。"""
    groups = defaultdict(list)
    for a in articles:
        groups[a.category].append(a)

    result = {}
    for category in CATEGORY_NAMES:
        cat_articles = groups.get(category, [])
        dated = [a for a in cat_articles if a.published is not None]
        undated = [a for a in cat_articles if a.published is None]
        dated.sort(key=lambda a: a.published, reverse=True)

        # 每个来源只取最新一条，保证 10 条新闻各来自不同来源
        seen_sources = set()
        top_articles = []
        for a in dated + undated:
            if a.source not in seen_sources:
                seen_sources.add(a.source)
                top_articles.append(a)
            if len(top_articles) >= MAX_ARTICLES_PER_CATEGORY:
                break
        result[category] = top_articles

    return result


def _build_json_data(date_str: str, categorized: dict) -> dict:
    """构建输出 JSON 数据结构。"""
    categories_json = {}
    for cat_key, cat_names in CATEGORY_NAMES.items():
        articles = categorized.get(cat_key, [])
        categories_json[cat_key] = {
            "name_zh": cat_names["zh"],
            "name_en": cat_names["en"],
            "articles": [
                {
                    "summary_zh": getattr(a, "summary_zh", a.summary),
                    "summary_en": getattr(a, "summary_en", a.summary),
                    "source": a.source,
                    "url": a.url,
                    "published": a.published.isoformat() if a.published else None,
                }
                for a in articles
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
        print(f"  {name}: {len(cat_articles)} 篇")

    # 3. 翻译
    all_selected = []
    for cat_articles in categorized.values():
        all_selected.extend(cat_articles)
    translate_articles(all_selected)

    # 4. 写入 JSON
    data_dir = _ensure_data_dir()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_data = _build_json_data(today, categorized)

    json_path = os.path.join(data_dir, f"{today}.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 5. 更新索引
    all_dates = _update_index(data_dir, today)

    print(f"\n数据文件: {json_path}")
    print(f"索引文件: 共 {len(all_dates)} 个日期")
    print("完成!")


if __name__ == "__main__":
    main()
