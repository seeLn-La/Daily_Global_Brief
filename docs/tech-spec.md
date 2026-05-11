# 技术规范

## 技术栈

| 层         | 选型                                    | 说明                         |
| ---------- | --------------------------------------- | ---------------------------- |
| 定时执行   | GitHub Actions (cron `0 23 * * *`)      | UTC 23:00 = 北京时间 7:00（提前1h缓冲GitHub延迟）     |
| 新闻抓取   | Python `feedparser` 库                  | 免费解析 RSS/Atom            |
| 翻译       | `deep-translator` (GoogleTranslator)    | 免费，无需 API Key           |
| 数据存储   | JSON 文件 (`data/YYYY-MM-DD.json`)      | Git 友好，Pages 直接读取     |
| 网页托管   | GitHub Pages (main 分支根目录)          | 免费，零部署                 |
| 推送       | Bark App REST API                       | `POST https://api.day.app/{key}/{title}/{body}` |

## 项目结构

```
news/
├── CLAUDE.md                      # Claude 工作指引
├── docs/                          # 项目文档
│   ├── requirements.md            # 需求文档
│   ├── tech-spec.md               # 技术规范（本文）
│   ├── design-spec.md             # UI 设计规范
│   └── execution-plan.md          # 分阶段执行计划
├── dev-log/                       # 开发日志（每日自动记录）
│   └── YYYY-MM-DD.md
├── index.html                     # Web UI（单文件，内嵌 CSS+JS）
├── scripts/                       # Python 脚本
│   ├── requirements.txt           # Python 依赖
│   ├── config.py                  # RSS 源配置
│   ├── fetcher.py                 # RSS 抓取模块
│   ├── translator.py              # 翻译模块
│   ├── aggregator.py              # 主编排脚本
│   └── bark_pusher.py             # Bark 推送模块
├── data/                          # 新闻数据（由脚本生成）
│   ├── index.json                 # 日期清单
│   └── YYYY-MM-DD.json           # 每日新闻
├── .github/workflows/
│   └── daily-news.yml             # Cron 工作流
└── .gitignore
```

## 数据流

```
RSS Feeds (15 sources)
  → fetcher.py (fetch + parse + dedup)
    → aggregator.py (categorize + sort + top 10)
      → translator.py (bilingual translation)
        → data/YYYY-MM-DD.json (write)
          → bark_pusher.py (push notification)
          → index.html (web rendering, via GitHub Pages)
```

## JSON 数据格式

### data/YYYY-MM-DD.json

```json
{
  "date": "2026-05-06",
  "generated_at": "2026-05-06T00:05:30Z",
  "categories": {
    "technology": {
      "name_zh": "科技",
      "name_en": "Technology",
      "articles": [
        {
          "summary_zh": "苹果发布搭载M4芯片的新款MacBook Pro",
          "summary_en": "Apple launches M4 MacBook Pro",
          "source": "TechCrunch",
          "url": "https://example.com/article",
          "published": "2026-05-06T08:30:00Z"
        }
      ]
    },
    "business": { ... },
    "ai": { ... }
  }
}
```

### data/index.json

```json
["2026-05-01", "2026-05-02", "2026-05-03"]
```

## RSS 源配置

中文源提供原生中文内容（只需英译一个方向），英文源只需中译一个方向。

### 科技 (Technology)
| 来源          | 语言 | RSS URL                                   |
| ------------- | ---- | ----------------------------------------- |
| TechCrunch    | EN   | `https://techcrunch.com/feed/`            |
| The Verge     | EN   | `https://www.theverge.com/rss/index.xml`  |
| Ars Technica  | EN   | `https://feeds.arstechnica.com/arstechnica/index` |
| Wired         | EN   | `https://www.wired.com/feed/rss`          |
| Hacker News   | EN   | `https://hnrss.org/frontpage`             |
| 极客公园      | ZH   | `https://www.geekpark.net/rss`            |
| 36氪          | ZH   | `https://36kr.com/feed`                   |

### 商业 (Business)
| 来源              | 语言 | RSS URL                                   |
| ----------------- | ---- | ----------------------------------------- |
| CNBC              | EN   | `https://www.cnbc.com/id/100003114/device/rss/rss.html` |
| Reuters (via GNews)| EN   | `https://news.google.com/rss/search?q=site:reuters.com+business` |
| Business Insider  | EN   | `https://www.businessinsider.com/rss`     |

### AI 发展 (AI)
| 来源                   | 语言 | RSS URL                                   |
| ---------------------- | ---- | ----------------------------------------- |
| MIT Technology Review  | EN   | `https://www.technologyreview.com/feed/`  |
| VentureBeat AI         | EN   | `https://venturebeat.com/category/ai/feed/` |
| 机器之心               | ZH   | `https://www.jiqizhixin.com/rss`          |
| 量子位                 | ZH   | `https://www.qbitai.com/feed`             |

## 翻译降级策略

```
deep-translator (GoogleTranslator)
  ↓ 失败
translate 库 (备选)
  ↓ 失败
原文降级（标记 translation_quality: "fallback"）
```

每次翻译调用间隔 0.5 秒，防止限速。

## 容错设计

| 场景                | 处理                                       |
| ------------------- | ------------------------------------------ |
| 单个 RSS 源超时     | 10s 超时，跳过该源，继续处理其他源         |
| 全部 RSS 源失败     | 写空 JSON，跳过推送，workflow 标记成功     |
| 翻译失败            | 降级链 → 最终原文                          |
| 当日无新文章        | 空 articles，跳过推送                      |
| Bark 推送失败       | catch 异常，不影响 workflow                 |
