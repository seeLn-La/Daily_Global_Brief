# 技术规范

## 技术栈

| 层         | 选型                                    | 说明                         |
| ---------- | --------------------------------------- | ---------------------------- |
| 定时执行   | GitHub Actions (cron `0 23 * * *`)      | UTC 23:00 = 北京时间 7:00（提前1h缓冲GitHub延迟）     |
| 新闻抓取   | Python `feedparser` + `requests` + 并发抓取 | 免费解析 RSS/Atom，支持并发与坏源跳过 |
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
RSS Feeds (28 sources)
  → fetcher.py (parallel fetch + parse + dedup + source health)
  → aggregator.py (categorize + enlarged candidate pool + event dedup + up to 10)
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
          "published": "2026-05-06T08:30:00Z",
          "selection_tier": "strong_match",
          "selection_reason": "高相关且来源优先",
          "selection_score": 7.5
        }
      ],
      "candidates": [
        {
          "summary": "苹果发布搭载M4芯片的新款MacBook Pro",
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
| MIT Technology Review | EN | `https://www.technologyreview.com/feed/` |
| Engadget      | EN   | `https://www.engadget.com/rss.xml`        |
| 极客公园      | ZH   | `https://www.geekpark.net/rss`            |
| 36氪          | ZH   | `https://36kr.com/feed`                   |
| 爱范儿        | ZH   | `https://www.ifanr.com/feed`              |

### 商业 (Business)
| 来源              | 语言 | RSS URL                                   |
| ----------------- | ---- | ----------------------------------------- |
| CNBC              | EN   | `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114` |
| Reuters (via GNews)| EN   | `https://news.google.com/rss/search?q=site:reuters.com+business` |
| BBC Business      | EN   | `https://feeds.bbci.co.uk/news/business/rss.xml` |
| MarketWatch       | EN   | `https://www.marketwatch.com/rss/topstories` |
| NYT Business      | EN   | `https://rss.nytimes.com/services/xml/rss/nyt/Business.xml` |
| Economist Finance  | EN   | `https://www.economist.com/finance-and-economics/rss.xml` |
| Business Insider  | EN   | `https://www.businessinsider.com/rss`     |
| Bloomberg Markets | EN   | `https://feeds.bloomberg.com/markets/news.rss` |
| Bloomberg Business| EN   | `https://feeds.bloomberg.com/business/news.rss` |
| Yahoo Finance     | EN   | `https://news.yahoo.com/rss/finance`      |

### AI 发展 (AI)
| 来源                   | 语言 | RSS URL                                   |
| ---------------------- | ---- | ----------------------------------------- |
| OpenAI News            | EN   | `https://openai.com/news/rss.xml`         |
| NVIDIA Developer Blog  | EN   | `https://developer.nvidia.com/blog/feed/` |
| MIT AI News            | EN   | `https://news.mit.edu/rss/topic/artificial-intelligence2` |
| TechCrunch AI          | EN   | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| The Decoder            | EN   | `https://the-decoder.com/feed/`           |
| 量子位                 | ZH   | `https://www.qbitai.com/feed`             |
| TechXplore             | EN   | `https://techxplore.com/rss-feed/machine-learning-ai-news/` |
| AI Business            | EN   | `https://aibusiness.com/rss.xml`          |
| KDnuggets              | EN   | `https://www.kdnuggets.com/feed`          |

## 翻译降级策略

```
deep-translator (GoogleTranslator)
  ↓ 失败
translate 库 (备选)
  ↓ 失败
原文降级（标记 translation_quality: "fallback"）
```

每次翻译调用间隔 0.5 秒，防止限速。

## 抓取容错策略

| 场景                | 处理                                       |
| ------------------- | ------------------------------------------ |
| 单个 RSS 源超时     | 记录失败，继续并发抓取其他源               |
| 单个 RSS 源 403     | 记录失败，连续多次后临时跳过               |
| RSS 解析异常        | 记录失败，继续处理其他源                   |
| 连续失败的来源      | 写入 `data/source_health.json` 并临时跳过   |
| 并发任务异常        | 单独捕获，不影响其他源                     |

## 新闻事件去重策略

去重在单个板块内执行，避免科技、商业、AI 板块之间因主题交叉而误删。候选文章仍按相关性、来源质量和时效性排序，因此重复事件默认保留排序更靠前的一篇。

### 两级去重

| 阶段       | 判断方式                                     | 处理方式                         |
| ---------- | -------------------------------------------- | -------------------------------- |
| 候选池     | URL 相同，或清洗后的标题完全相同             | 只保留排序更靠前的一篇           |
| 最终 10 篇 | 标题字符相似度高，或有效词语重合度高         | 视为同一事件，跳过后继续向后补位 |

### 标题处理规则

1. 使用 Unicode NFKC 统一字符形式，并转换为小写。
2. 去除标点、多余空格和常见新闻前缀，减少格式差异。
3. 使用 Python 标准库 `difflib.SequenceMatcher` 计算字符相似度。
4. 对英文标题中的常见新闻动作进行归一化，例如将 `acquire`、`acquired`、`acquires` 和 `buys` 统一为“收购”动作。
5. 同时计算有效词语重合度；只有共同出现关键名称和相同动作并达到保守阈值，才判定为同一事件，降低误删风险。
6. 每次去重输出跳过数量及对应标题，便于检查规则是否过严。

该策略不调用 AI/LLM API，不新增第三方依赖。措辞差异特别大的跨语言标题可能无法完全识别，后续可根据每日结果调整阈值。

## 周末数量策略

- 周六、周日抓取最近 7 天；周一抓取最近 4 天，覆盖周末回顾窗口。
- 候选池每分类最多保留 50 篇、每来源最多保留 4 篇，给跨来源去重和分层补位留下空间。
- AI 发展模块优先官方发布和研究论文，不足时使用媒体原创报道；社区转载不作为补位来源。
- 最终数量上限为 10 篇。合格且不重复的事件不足 10 篇时保留实际数量，不重复展示旧事件或降低来源门槛。
- 页面显示实际 verified 数量，并在周末数量不足时说明扩展窗口和补位规则。

## 容错设计

| 场景                | 处理                                       |
| ------------------- | ------------------------------------------ |
| 单个 RSS 源超时     | 10s 超时，跳过该源，继续处理其他源         |
| 全部 RSS 源失败     | 写空 JSON，跳过推送，workflow 标记成功     |
| 翻译失败            | 降级链 → 最终原文                          |
| 当日无新文章        | 空 articles，跳过推送                      |
| Bark 推送失败       | catch 异常，不影响 workflow                 |
