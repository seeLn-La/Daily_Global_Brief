# CLAUDE.md — Daily News Aggregation System

## 项目概述

面向商业分析从业者的全球新闻聚合系统。每日自动抓取科技、商业、AI 新闻，中英双语展示，Bark 推送到 iPhone。

## 用户背景

用户不懂代码（商业分析从业者），沟通时需用通俗语言解释技术决策，避免使用行话。关键决策需先说明利弊再等待确认。

## 标准文件路径

| 用途         | 路径                                |
| ------------ | ----------------------------------- |
| 需求文档     | `docs/requirements.md`              |
| 技术规范     | `docs/tech-spec.md`                 |
| UI 设计规范  | `docs/design-spec.md`               |
| 执行计划     | `docs/execution-plan.md`            |
| 开发日志     | `dev-log/YYYY-MM-DD.md`             |
| Python 脚本  | `scripts/*.py`                      |
| Python 依赖  | `scripts/requirements.txt`          |
| 新闻数据     | `data/YYYY-MM-DD.json`              |
| 日期索引     | `data/index.json`                   |
| CI/CD 工作流 | `.github/workflows/daily-news.yml`  |
| Web UI       | `index.html`                        |

## 工作规范

### 执行方式

- **每完成一个文件即暂停**，等待用户确认后再继续下一个
- **不要一口气做完所有文件**，分阶段推进
- **每个阶段结束后**，更新 `docs/execution-plan.md` 中的勾选状态

### 开发日志

- 每次编码会话结束后，在 `dev-log/` 下以当天日期创建或更新日志文件
- 日志内容包括：已完成事项、待办事项、决策记录
- 日志文件命名格式：`dev-log/YYYY-MM-DD.md`

### 文档优先

- 修改功能前，先参考 `docs/` 中的对应文档
- 如需求变更，同步更新 `docs/requirements.md`
- 如技术方案调整，同步更新 `docs/tech-spec.md`
- 如 UI 设计变化，同步更新 `docs/design-spec.md`

### 代码原则

- 每个 Python 脚本单一职责，可独立测试
- 不引入不必要的抽象或第三方依赖
- 容错优先：单个模块失败不影响整体流程
- 中文注释、英文变量名

### 格式规范

- **已完成任务不打删除线**：`- [x]` 完成项不使用 `~~删除线~~` 标记，保持文本干净可读
- 全库通用规范，所有 `.md` 文件均适用

### 安全提醒

- `BARK_DEVICE_KEY` 存储在 GitHub Secrets，不硬编码到任何文件中
- `.gitignore` 需忽略 `__pycache__/`、`.DS_Store`、`venv/` 等

## 实施阶段（详见 docs/execution-plan.md）

0. 项目文档体系 ✅
1. Python 核心脚本（config → fetcher → translator → aggregator → bark_pusher）
2. GitHub Actions 工作流
3. Web UI (index.html)
4. 端到端验证

## 关键约束

- 每日执行 **不消耗 AI/LLM API Token**
- 部署在 **GitHub Actions + Pages（免费）**
- 推送渠道：**Bark App（iOS）**
- 定时触发：**UTC 23:00 = 北京时间 7:00**（提前1小时缓冲GitHub Actions延迟）
- 摘要来源：**RSS 标题清洗 + 截断**（非 AI 生成）
- 翻译方式：**deep-translator 免费库**（非 API）
