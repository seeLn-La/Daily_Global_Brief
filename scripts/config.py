# 每分类最多选取文章数
MAX_ARTICLES_PER_CATEGORY = 10

# 摘要最大字符数
SUMMARY_MAX_LENGTH = 30

# RSS 源请求超时（秒）
FEED_TIMEOUT = 10

# 翻译请求间隔（秒）
TRANSLATION_DELAY = 0.5

# 数据输出目录
DATA_DIR = "data"

# RSS 源配置
# 每个源包含: url, category (technology/business/ai)
RSS_SOURCES = [
    # ===== 科技 (Technology) — 10 源 =====
    {"url": "https://techcrunch.com/feed/", "category": "technology"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "technology"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "category": "technology"},
    {"url": "https://www.wired.com/feed/rss", "category": "technology"},
    {"url": "https://www.technologyreview.com/feed/", "category": "technology"},
    {"url": "https://hnrss.org/frontpage", "category": "technology"},
    {"url": "https://36kr.com/feed", "category": "technology"},
    {"url": "https://www.tmtpost.com/feed", "category": "technology"},
    {"url": "https://www.ifanr.com/feed", "category": "technology"},
    {"url": "https://www.geekpark.net/rss", "category": "technology"},

    # ===== 商业 (Business) — 10 源 =====
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "category": "business"},
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "category": "business"},
    {"url": "https://news.yahoo.com/rss/finance", "category": "business"},
    {"url": "https://feeds.bloomberg.com/markets/news.rss", "category": "business"},
    {"url": "https://moxie.foxbusiness.com/google-publisher/latest.xml", "category": "business"},
    {"url": "https://www.marketwatch.com/rss/topstories", "category": "business"},
    {"url": "https://feeds.bloomberg.com/business/news.rss", "category": "business"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "category": "business"},
    {"url": "https://www.economist.com/finance-and-economics/rss.xml", "category": "business"},
    {"url": "https://www.businessinsider.com/rss", "category": "business"},

    # ===== AI 发展 (AI) — 10 源 =====
    {"url": "https://www.artificialintelligence-news.com/feed/", "category": "ai"},
    {"url": "https://openai.com/news/rss.xml", "category": "ai"},
    {"url": "https://developer.nvidia.com/blog/feed/", "category": "ai"},
    {"url": "https://news.mit.edu/rss/topic/artificial-intelligence2", "category": "ai"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "ai"},
    {"url": "https://www.qbitai.com/feed", "category": "ai"},
    {"url": "https://zhidx.com/rss", "category": "ai"},
    {"url": "https://techxplore.com/rss-feed/machine-learning-ai-news/", "category": "ai"},
    {"url": "https://huggingface.co/blog/feed.xml", "category": "ai"},
    {"url": "https://aibusiness.com/rss.xml", "category": "ai"},
]

# 分类名称映射
CATEGORY_NAMES = {
    "technology": {"zh": "科技", "en": "Technology"},
    "business": {"zh": "商业", "en": "Business"},
    "ai": {"zh": "AI 发展", "en": "AI Development"},
}
