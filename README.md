# Daily Global Brief

An automated bilingual news brief covering technology, business, and artificial intelligence.

The project collects news from trusted RSS sources, classifies and deduplicates articles, presents them in English and Chinese, publishes a daily web brief, and sends a concise summary to iPhone through Bark.

## Live Demo

[Open Daily Global Brief](https://seeln-la.github.io/news/)

## Key Features

- Daily aggregation of technology, business, and AI news
- English and Chinese bilingual presentation
- Source-quality labels: Official Release, Research Paper, Original Reporting, and Community Source
- Content-based classification instead of relying only on source categories
- Cross-day deduplication to prevent the same story from appearing repeatedly
- Error-page filtering to prevent RSS error pages from becoming fake news
- Weekend AI coverage using a wider 72-hour window
- Responsive web interface with date navigation
- Bark notifications for iPhone
- Automated deployment through GitHub Actions and GitHub Pages

## Source Quality

The system prioritizes first-party and research sources for AI coverage, including:

- OpenAI
- Google Research
- Google DeepMind
- NVIDIA
- AWS Machine Learning
- Microsoft Research
- Hugging Face
- Apple Machine Learning Research
- arXiv

AI articles are only included in the final AI section when they come from official sources or original research. This prevents media summaries and community posts from dominating the AI category.

## How It Works

```text
RSS Sources
    ↓
Concurrent Fetching
    ↓
Date and Error-Page Validation
    ↓
Content-Based Classification
    ↓
Cross-Source and Cross-Day Deduplication
    ↓
Bilingual Output
    ↓
GitHub Pages + Bark Notification
```

## Technical Design

- Python-based news processing pipeline
- RSS and Atom feed parsing
- Free translation through `deep-translator`
- No paid LLM or AI API tokens required
- GitHub Actions for daily scheduled execution
- GitHub Pages for public hosting
- Bark for iPhone notifications
- Beijing-time-aware date handling
- Fault-tolerant source fetching and health monitoring

## News Selection Rules

- Technology, business, and AI categories are determined using article content and title signals
- Source-level categories are treated as weak references rather than absolute rules
- Articles are ranked by topical relevance, recency, and source quality
- Similar articles from different sources are merged or filtered
- Articles already used in the previous three days are deprioritized
- The system aims to provide up to ten articles per category
- Source quality is prioritized over artificially filling the list

## Repository Structure

```text
.
├── data/                       # Daily generated news data
├── docs/                       # Requirements and technical documentation
├── dev-log/                    # Development history
├── scripts/
│   ├── config.py               # RSS source configuration
│   ├── fetcher.py              # Feed fetching and validation
│   ├── aggregator.py           # Classification, ranking, and deduplication
│   ├── translator.py           # English-Chinese translation
│   ├── bark_pusher.py          # Bark notification delivery
│   └── noon_push.py            # Local scheduled push script
├── index.html                  # Web interface
└── .github/workflows/          # GitHub Actions automation
```

## Automation

The daily workflow automatically:

1. Fetches the latest RSS articles
2. Filters invalid dates and RSS error pages
3. Classifies articles into three categories
4. Removes duplicate and low-quality items
5. Generates bilingual JSON data
6. Publishes the result to GitHub Pages
7. Prepares a Bark notification summary

## Project Goals

This project is designed for professionals who need a fast, reliable overview of global technology, business, and AI developments without manually checking dozens of websites every day.

The main priorities are:

- Reliable source quality
- Clear category boundaries
- Low operating cost
- Transparent processing rules
- Minimal maintenance
- Fast access to original articles
