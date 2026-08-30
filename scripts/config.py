# 每分类最多选取文章数
MAX_ARTICLES_PER_CATEGORY = 10

# 每分类最多保留的候选文章数
MAX_CANDIDATES_PER_CATEGORY = 50

# 每个来源在候选池中最多保留几篇
MAX_CANDIDATES_PER_SOURCE = 4

# RSS 源请求超时（秒）
FEED_TIMEOUT = 10

# 翻译请求间隔（秒）
TRANSLATION_DELAY = 0.2

# 数据输出目录
DATA_DIR = "data"

# RSS 源配置
# 每个源包含: url, category (technology/business/ai), source_type
# 说明：
# - first_party: 公司、研究机构或政府机构自己发布的原始内容
# - research: 论文或研究团队原始发布，周末可作为 AI 内容补位
# - original_reporting: 媒体自己的原创报道，不经过新闻聚合器转发
# - community: 社区链接聚合，仅作为低优先级补位
RSS_SOURCES = [
    # ===== 科技 (Technology) =====
    {"url": "https://www.apple.com/newsroom/rss-feed.rss", "category": "technology", "source_type": "first_party"},
    {"url": "https://blog.cloudflare.com/rss/", "category": "technology", "source_type": "first_party"},
    {"url": "https://github.blog/feed/", "category": "technology", "source_type": "first_party"},
    {"url": "https://hacks.mozilla.org/feed/", "category": "technology", "source_type": "first_party"},
    {"url": "https://techcrunch.com/feed/", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://feeds.arstechnica.com/arstechnica/index", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://www.wired.com/feed/rss", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://www.technologyreview.com/feed/", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://www.engadget.com/rss.xml", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://36kr.com/feed", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://www.ifanr.com/feed", "category": "technology", "source_type": "original_reporting"},
    {"url": "https://hnrss.org/frontpage", "category": "technology", "source_type": "community"},

    # ===== 商业 (Business) =====
    {"url": "https://www.sec.gov/news/pressreleases.rss", "category": "business", "source_type": "first_party"},
    {"url": "https://www.federalreserve.gov/feeds/press_all.xml", "category": "business", "source_type": "first_party"},
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "category": "business", "source_type": "original_reporting"},
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "category": "business", "source_type": "original_reporting"},
    {"url": "https://www.marketwatch.com/rss/topstories", "category": "business", "source_type": "original_reporting"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", "category": "business", "source_type": "original_reporting"},
    {"url": "https://www.economist.com/finance-and-economics/rss.xml", "category": "business", "source_type": "original_reporting"},
    {"url": "https://www.businessinsider.com/rss", "category": "business", "source_type": "original_reporting"},
    {"url": "https://feeds.bloomberg.com/markets/news.rss", "category": "business", "source_type": "original_reporting"},
    {"url": "https://feeds.bloomberg.com/business/news.rss", "category": "business", "source_type": "original_reporting"},

    # ===== AI 发展 (AI) =====
    # 公司与研究机构官方发布
    {"url": "https://openai.com/news/rss.xml", "category": "ai", "source_type": "first_party"},
    {"url": "https://deepmind.google/blog/rss.xml", "category": "ai", "source_type": "first_party"},
    {"url": "https://research.google/blog/rss/", "category": "ai", "source_type": "first_party"},
    {"url": "https://blog.google/technology/ai/rss/", "category": "ai", "source_type": "first_party"},
    {"url": "https://www.microsoft.com/en-us/research/feed/", "category": "ai", "source_type": "first_party"},
    {"url": "https://developer.nvidia.com/blog/feed/", "category": "ai", "source_type": "first_party"},
    {"url": "https://aws.amazon.com/blogs/machine-learning/feed/", "category": "ai", "source_type": "first_party"},
    {"url": "https://huggingface.co/blog/feed.xml", "category": "ai", "source_type": "first_party"},
    # 原始研究：周末用于补充模型、方法和实验进展，不伪装成媒体新闻
    {"url": "https://rss.arxiv.org/rss/cs.AI", "category": "ai", "source_type": "research"},
    {"url": "https://rss.arxiv.org/rss/cs.LG", "category": "ai", "source_type": "research"},
    {"url": "https://machinelearning.apple.com/rss.xml", "category": "ai", "source_type": "first_party"},
    # 媒体原创报道：只作补位，不作为一手来源
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "ai", "source_type": "original_reporting"},
]

# 分类名称映射
CATEGORY_NAMES = {
    "technology": {"zh": "科技", "en": "Technology"},
    "business": {"zh": "商业", "en": "Business"},
    "ai": {"zh": "AI 发展", "en": "AI Development"},
}
