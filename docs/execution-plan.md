# 分阶段执行计划

## 阶段总览

| 阶段 | 内容                       | 文件数 | 状态   |
| ---- | -------------------------- | ------ | ------ |
| 0    | 项目文档体系 + CLAUDE.md   | 6      | ✅ 完成 |
| 1    | Python 核心脚本（5文件）   | 5      | 待开始 |
| 2    | GitHub Actions 工作流      | 1      | 待开始 |
| 3    | Web UI（index.html）       | 1      | 待开始 |
| 4    | 测试验证                   | -      | 待开始 |

## 阶段 0：项目基础设施 ✅

- [x] `docs/requirements.md` — 需求文档
- [x] `docs/tech-spec.md` — 技术规范
- [x] `docs/design-spec.md` — UI 设计规范
- [x] `docs/execution-plan.md` — 执行计划（本文档）
- [ ] `CLAUDE.md` — Claude 工作指引
- [ ] `dev-log/` — 开发日志目录

## 阶段 1：Python 核心脚本

按依赖顺序执行（每个文件独立开发，确认无误后进入下一个）：

1. **`scripts/requirements.txt`** — Python 依赖声明
2. **`scripts/config.py`** — RSS 源配置 + 常量
3. **`scripts/fetcher.py`** — RSS 抓取 + 解析 + 去重
4. **`scripts/translator.py`** — 中英互译 + 降级策略
5. **`scripts/aggregator.py`** — 主编排脚本（调用 fetcher + translator）
6. **`scripts/bark_pusher.py`** — Bark 推送

**⚠ 阶段 1 确认点**：本地运行 `python scripts/aggregator.py`，检查 `data/` 目录是否生成正确 JSON。

## 阶段 2：GitHub Actions

7. **`.github/workflows/daily-news.yml`** — 定时任务定义
8. **`.gitignore`** — Git 忽略规则

**⚠ 阶段 2 确认点**：推送到 GitHub，手动触发 workflow，观察 Actions 日志。

## 阶段 3：Web UI

9. **`index.html`** — 单文件网页（HTML + CSS + JS）

**⚠ 阶段 3 确认点**：GitHub Pages 开启后，浏览器访问验证三列展示、日期切换、响应式布局。

## 阶段 4：端到端验证

10. GitHub Pages 确认可访问
11. 手动触发 workflow，验证 Bark 推送到达手机
12. 等待首次 cron 触发（次日北京时间 8:00），验证准时推送

## 开发原则

- **每完成一个文件即暂停**，由用户确认后再继续
- **不在一个阶段内跨文件同时修改**
- **每次修改后记录 dev-log**
- **不跳过确认点**
