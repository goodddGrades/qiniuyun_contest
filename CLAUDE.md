# 项目规范（比赛用）

## 项目信息
- 项目名称：AI 小说转剧本工具
- GitHub 仓库：(https://github.com/goodddGrades/qiniuyun_contest.git)
- 队友 GitHub 账号：2719405535@qq.com
- 比赛题目：AI小说转剧本工具 很多小说作者希望将自己的作品 改编成剧本，请开发一款 AI辅助 剧本创作工具，降低改编门槛 提升效率。 要求：能将3个章节以上的小 说文本自动转换为结构化剧本 (YAML 格式），让作者可以快 速获得可编辑、可进一步打磨的 剧本初稿。请额外写一篇文档， 定义剧本的 YAML Schema。文 档中需说明该 Schema 的设计原 因。
## 极其重要事项须知
### PR（Pull Request）提交规范
1.请基于PR添加新功能。
2.每个PR只做一件事：每个PR只实现或修改单一功能；鼓励尽可能小、粒度尽可能细的PR；大功能应拆分为多个独立PR分步提交。
3.PR标题与描述需清晰完整，内容包含：
- 标题：一句话说明本PR新增/修改了什么。
- 功能描述：说明该功能的作用与使用方式。
- 实现思路：简要说明技术选型或核心实现逻辑。
- 测试方式：如何验证该功能正常运行。
4.PR合并后，主分支代码需保持可运行状态，评委在任意时间查看应能复现演示效果。
## Git 流程（给队友看，也是给我的规矩）

### 基本概念
- **main 分支**：稳定版本，不能直接改
- **feature/xxx 分支**：开发新功能用的分支
- **PR（Pull Request）**：写完代码先提 PR，队友看完没问题再合并

### 我（Claude Code）的 Git 行为规则
1. **不直接推 main 分支**，必须先提 PR
2. 每次开始写代码前，先拉取最新代码
3. Commit 信息写清楚改了啥（中文）
4. 如果我创建了 PR，会告诉你链接，你去确认合并

### 工作流程
```
你跟我说写什么功能
  ↓
我基于 main 创建 feature/xxx 分支
  ↓
我写代码、commit、push
  ↓
我在 GitHub 上提 PR（或者告诉你让我提）
  ↓
你和队友 Review 代码
  ↓
没问题 → 合并到 main
```

## 给我的限制（你说了算）

### 🔴 绝对不能做的事
- ~~不改 `.env` 文件~~（含有密码密钥）
- ~~不改队友负责的模块~~（除非你主动说）
- ~~不删你电脑上的任何文件~~（除非你确认）
- ~~不推送到不是你说的仓库地址~~

### 🟡 必须先问你再做的事
- 涉及项目架构的大改动
- 安装新的依赖包（pip install / npm install）
- 改数据库结构

### 🟢 我直接就能做的事
- 写代码实现功能
- 修 Bug
- 写测试
- 写文档
- 代码 Review（你看不懂的代码发给我看）
- 查 Git 历史、看 diff

## Git 提交须知（不应提交的文件）

以下文件/目录**只留在本地，不提交到 git**：

| 路径 | 原因 |
|------|------|
| `.claude/` | Claude Code 本地配置 |
| `instance/` | 运行时生成的剧本文件 |
| `.env` | API 密钥和敏感配置 |
| `__pycache__/` | Python 编译缓存 |
| `venv/` / `.venv/` | Python 虚拟环境 |
| `.gitignore` | 已包含上述所有规则 |

**规范**：每次 `git add` 前先跑 `git status` 检查，只 `git add` 项目代码文件（.py, .html, .css, .js, .md, requirements.txt），不要无脑 `git add .`。

## 技术栈
- 后端语言：Python 3.11
- Web框架：Flask 3.1 + Jinja2 模板
- AI模型：Claude API（Anthropic SDK）
- 数据格式：YAML（PyYAML）
- 测试工具：pytest

## 命令速查（给队友看）
```bash
# 拉最新代码
git pull

# 看当前在哪个分支
git branch

# 创建并切换到新分支
git checkout -b feature/xxx

# 查看改了什么
git status
git diff

# 暂存并提交
git add .
git commit -m "写了啥"

# 推送到 GitHub
git push origin 当前分支名

# 看有哪些分支
git branch -a
```

## 队友配合建议
如果队友不太熟 Git，可以这样用我：
1. 队友写好代码 push 到 GitHub
2. 你跟我说"帮我 review 一下队友的代码"
3. 我拉下来看，有问题告诉你
4. 你觉得没问题就合并

或者：
1. 你说"帮我写 xxx 功能"
2. 我写好推上去
3. 你让队友看看
4. 没问题，你点合并


