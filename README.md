# ✍️ 转笔为剧 — AI 小说转剧本工具

> 比赛题目：AI 辅助剧本创作工具  
> 将 3 章以上的小说文本自动转换为结构化剧本（YAML 格式），降低小说作者改编剧本的门槛。

---

## 📦 项目架构

```
novel_to_script/
├── __init__.py          # 包初始化
├── converter.py         # 🎯 核心转换引擎：调用 LLM 将小说转剧本
└── schema.py            # 📐 YAML Schema 定义 + 验证器

templates/               # 🎨 前端页面（Jinja2）
├── base.html            #    布局模板（导航 + 页脚）
├── index.html           #    首页：上传小说
├── result.html          #    结果页：展示转换后的 YAML
└── editor.html          #    编辑页：在线修改剧本

static/
├── css/style.css        # 🖌️ 样式
└── js/main.js           # ⚡ 前端交互

docs/
└── yaml_schema.md       # 📄 YAML Schema 设计文档（比赛要求）

tests/
├── __init__.py
└── test_converter.py    # 🧪 测试套件

app.py                   # 🚪 Flask 入口 / 路由
config.py                # ⚙️ 配置项
requirements.txt         # 📋 依赖清单
```

### 各模块说明

| 模块 | 作用 |
|------|------|
| `app.py` | Flask Web 应用入口，定义路由：上传 → 转换 → 展示 → 编辑 → 下载 |
| `config.py` | 读取 `.env` 中的 API Key 等配置 |
| `novel_to_script/converter.py` | 核心转换逻辑，调用 Claude API，支持分章处理、长文本分块、mock 模式 |
| `novel_to_script/schema.py` | 定义剧本 YAML 格式规范，提供结构验证函数 |
| `templates/` | 4 个 Jinja2 页面模板，覆盖完整用户流程 |
| `docs/yaml_schema.md` | 比赛要求的 YAML Schema 设计文档，含设计原因说明 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

创建 `.env` 文件：

```env
ANTHROPIC_API_KEY=你的Claude_API_Key
```

> 没有 API Key 也能运行，会自动使用 mock 数据展示效果。

### 3. 启动

```bash
python app.py
```

浏览器访问 `http://localhost:5000`

---

## 📝 使用方法

1. **上传小说** — 在首页粘贴你的小说文本（至少 3 章，用「第X章」分隔）
2. **一键转换** — 点击「开始转换」，AI 自动分析并生成结构化剧本
3. **查看结果** — 预览转换后的 YAML 剧本
4. **在线编辑** — 在编辑器里直接修改 YAML 内容
5. **下载 YAML** — 导出为 `.yaml` 文件

---

## 📐 YAML Schema 概要

```yaml
剧本:
  元数据:         # 标题、原作、作者、章节数、日期
  角色表:         # 角色名、年龄、性别、性格、简介
  幕:             # 幕号、幕标题
    场:           # 场号、场景、时间、人物
      内容:       # 对白 / 动作描写 / 舞台指示
```

详细设计文档见 [`docs/yaml_schema.md`](docs/yaml_schema.md)

---

## 🧪 测试

```bash
pytest
```

---

## 🔄 开发流程

本项目严格按照 Git Feature Branch 流程开发：

```
1. 有新功能需求
       ↓
2. 基于 main 开 feature/xxx 分支
       ↓
3. 写代码 → commit → push
       ↓
4. 创建 PR（每个 PR 只做一个功能）
       ↓
5. Review → 合并到 main
```

### 分支命名

| 分支 | 用途 |
|------|------|
| `main` | 稳定版本，随时可运行演示 |
| `feature/xxx` | 新功能开发 |
| `fix/xxx` | Bug 修复 |

### 技术栈

- **后端**：Python 3.11 + Flask 3.1
- **前端**：Jinja2 模板 + 原生 CSS/JS
- **AI 模型**：Claude API（Anthropic SDK）
- **数据格式**：YAML（PyYAML）
- **测试**：pytest

---

## 👥 团队

- GitHub 组织：[goodddGrades](https://github.com/goodddGrades)
- 队友：2719405535@qq.com
