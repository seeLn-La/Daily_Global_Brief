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
    # ===== 科技 (Technology) =====
    {"url": "https://techcrunch.com/feed/", "category": "technology"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "technology"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "category": "technology"},
    {"url": "https://www.wired.com/feed/rss", "category": "technology"},
    {"url": "https://hnrss.org/frontpage", "category": "technology"},
    {"url": "https://www.geekpark.net/rss", "category": "technology"},
    {"url": "https://36kr.com/feed", "category": "technology"},

    # ===== 商业 (Business) =====
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "category": "business"},
    {"url": "https://feeds.reuters.com/reuters/businessNews", "category": "business"},
    {"url": "https://www.businessinsider.com/rss", "category": "business"},

    # ===== AI 发展 (AI) =====
    {"url": "https://www.technologyreview.com/feed/", "category": "ai"},
    {"url": "https://venturebeat.com/category/ai/feed/", "category": "ai"},
    {"url": "https://www.jiqizhixin.com/rss", "category": "ai"},
    {"url": "https://www.qbitai.com/feed", "category": "ai"},
]

# 分类名称映射
CATEGORY_NAMES = {
    "technology": {"zh": "科技", "en": "Technology"},
    "business": {"zh": "商业", "en": "Business"},
    "ai": {"zh": "AI 发展", "en": "AI Development"},
}
