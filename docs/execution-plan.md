# 分阶段执行计划

## 阶段总览

| 阶段 | 内容                       | 文件数 | 状态     |
| ---- | -------------------------- | ------ | -------- |
| 0    | 项目文档体系 + CLAUDE.md   | 6      | ✅ 完成  |
| 1    | Python 核心脚本（5文件）   | 5      | ✅ 完成  |
| 2    | GitHub Actions 工作流      | 2      | ✅ 完成  |
| 3    | Web UI（index.html）       | 1      | ✅ 完成  |
| 4    | 端到端验证                 | -      | ✅ 完成  |

**项目已完成，于 2026-05-07 上线。**

## 阶段 0：项目基础设施 ✅

- [x] `docs/requirements.md` — 需求文档
- [x] `docs/tech-spec.md` — 技术规范
- [x] `docs/design-spec.md` — UI 设计规范
- [x] `docs/execution-plan.md` — 执行计划（本文档）
- [x] `CLAUDE.md` — Claude 工作指引
- [x] `dev-log/` — 开发日志目录

## 阶段 1：Python 核心脚本 ✅

1. `scripts/requirements.txt` — Python 依赖声明 ✅
2. `scripts/config.py` — RSS 源配置 + 常量 ✅
3. `scripts/fetcher.py` — RSS 抓取 + 解析 + 去重 ✅
4. `scripts/translator.py` — 中英互译 + 降级策略 + 超时控制 ✅
5. `scripts/aggregator.py` — 主编排脚本 + 跨来源同事件去重 + 自动补位 ✅
6. `scripts/bark_pusher.py` — Bark 推送 ✅

## 阶段 2：GitHub Actions ✅

7. `.github/workflows/daily-news.yml` — 定时任务定义 ✅
8. `.gitignore` — Git 忽略规则 ✅

## 阶段 3：Web UI ✅

9. `index.html` — Apple 极简风格单文件网页（三列响应式 + 日期导航 + 骨架屏/空/错误状态） ✅
10. 页面标题更新为 `Daily Global Brief`，副标题不再显示固定更新时间 ✅

## 阶段 4：端到端验证 ✅

11. GitHub 仓库: `seeLn-La/news` ✅
12. `BARK_DEVICE_KEY` secret 已配置 ✅
13. GitHub Pages 已开启: https://seeln-la.github.io/news/ ✅
14. 手动触发 workflow，验证 Bark 推送到达手机 ✅
15. Cron 触发：每日 UTC 0:00 = 北京时间 8:00，自动运行 ✅
16. 去重规则测试：相同标题、相似事件、正常新闻保留和 10 篇自动补位均通过 ✅
17. 历史候选数据检查：相似度阈值未发现明显误删 ✅

## 日常维护

- 无需任何人工操作，GitHub Actions 每日自动运行
- 在 `scripts/config.py` 的 `RSS_SOURCES` 列表可增删 RSS 源
- `scripts/fetcher.py` 会并发抓取，并自动跳过连续失败的来源
- `scripts/aggregator.py` 会过滤不同来源对同一事件的重复报道，并自动向后补位
- `data/source_health.json` 会记录坏源状态，系统会自动清理已移除的旧记录
- Push 到 GitHub 后自动部署网页
