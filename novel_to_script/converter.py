"""
核心转换逻辑

使用 LLM（默认 Claude API）将小说文本转换为结构化剧本 YAML。
采用两阶段策略：
  1. 分析阶段 — 提取全篇角色清单和整体结构
  2. 转换阶段 — 逐章转换，带上角色上下文确保一致性
"""

import re
import yaml
from datetime import datetime
from typing import Any

from config import Config
from novel_to_script.schema import get_empty_script

# -----------------------------------------------------------
# 提示词
# -----------------------------------------------------------

ANALYST_PROMPT = """你是一位专业的剧本改编分析师。你的任务是分析小说全文，提取以下信息：

1. **角色清单**：列出所有出现的人物，包括姓名、年龄（如已知）、性别、性格特征、角色简介
2. **整体结构**：判断故事大概分几幕，每幕的核心冲突是什么

只需输出角色清单，不要逐章转换。格式要求：

```yaml
角色表:
  - 角色名: 张三
    年龄: 30
    性别: 男
    性格特征: 勇敢、直率
    角色简介: 主角，一名侦探
```

尽可能识别所有角色，包括只出现过名字的配角。"""

CONVERTER_PROMPT = """你是一位专业的剧本改编专家。请将以下小说章节转换为结构化剧本格式。

已知本故事包含以下角色：
{character_context}

转换规则：
1. 小说中的叙述性文字 → 「动作描写」
2. 对话 → 「对白」，标注角色和表情/语气
3. 场景转换处 → 「舞台指示」（灯光、音效、场景切换）
4. 每章至少分为 2-4 场，场景切换即换场
5. 角色名必须与角色表中的名字完全一致

请严格按照此 YAML Schema 输出，只输出 YAML 代码块：

```yaml
幕:
  - 幕号: 1
    幕标题: <章节主题>
    场:
      - 场号: 1
        场景: <地点/场景名>
        时间: <时间描述>
        人物: [角色名列表]
        内容:
          - 类型: 动作描写
            内容: <动作/叙事描述>
          - 类型: 对白
            角色: <角色名>
            台词: <对话内容>
            表情: <表情或动作指示>
          - 类型: 舞台指示
            内容: <舞台效果说明>
```

现在请转换以下第 {chapter_num} 章内容："""


class NovelConverter:
    """小说→剧本转换器

    支持两种 LLM 后端：
      - Claude（Anthropic SDK）— 默认
      - DeepSeek（OpenAI 兼容接口）— 配置 DEEPSEEK_API_KEY 后自动切换
    """

    def __init__(self, api_key: str = ""):
        """api_key 参数保留向后兼容，实际使用 Config 自动检测"""
        self.provider = Config.LLM_PROVIDER
        self.client = None
        self._init_client()

    def _init_client(self):
        """根据配置初始化 LLM 客户端"""
        if self.provider == "deepseek" and Config.DEEPSEEK_API_KEY:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=Config.DEEPSEEK_API_KEY,
                    base_url=Config.DEEPSEEK_BASE_URL,
                )
            except Exception as e:
                print(f"DeepSeek 客户端初始化失败: {e}")
        elif Config.ANTHROPIC_API_KEY:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            except Exception as e:
                print(f"Anthropic 客户端初始化失败: {e}")

    def _call_llm(self, system: str, user: str, max_tokens: int = 4096) -> str:
        """统一的 LLM 调用接口，自动选择 Claude 或 DeepSeek"""
        if not self.client:
            return ""

        if self.provider == "deepseek":
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content or ""

        # Anthropic / Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    # -------------------------------------------------------
    # 公开接口
    # -------------------------------------------------------

    def convert(self, novel_text: str, title: str = "") -> dict[str, Any]:
        """
        将整部小说转换为剧本结构。

        参数：
            novel_text: 小说全文（含章节分隔）
            title:      剧本标题（可选）

        返回：
            符合 schema 的剧本字典
        """
        chapters = self._split_chapters(novel_text)
        result = get_empty_script()

        result["剧本"]["元数据"]["标题"] = title or "未命名剧本"
        result["剧本"]["元数据"]["原作"] = title or "未命名小说"
        result["剧本"]["元数据"]["改编章节数"] = len(chapters)
        result["剧本"]["元数据"]["转换日期"] = datetime.now().strftime(
            "%Y-%m-%d"
        )

        if not self.client:
            return self._mock_conversion(chapters, result)

        # --------------------------------------------------
        # 阶段1：分析全篇角色（取前 6000 字就够了）
        # --------------------------------------------------
        sample = novel_text[:6000]
        characters = self._extract_characters(sample)
        result["剧本"]["角色表"] = characters
        char_context = self._format_characters(characters)

        # --------------------------------------------------
        # 阶段2：逐章转换（带上角色上下文）
        # --------------------------------------------------
        for i, chapter in enumerate(chapters):
            act_data = self._convert_chapter_with_context(
                chapter, i + 1, char_context
            )
            result["剧本"]["幕"].append(act_data)

        # 后处理：确保角色表完整
        self._consolidate_characters(result, characters)

        return result

    # -------------------------------------------------------
    # 阶段1：角色提取
    # -------------------------------------------------------

    def _extract_characters(self, sample: str) -> list[dict]:
        """分析小说片段，提取角色清单"""
        try:
            content = self._call_llm(
                system=ANALYST_PROMPT,
                user=f"请分析以下小说片段，提取所有角色信息：\n\n{sample}",
                max_tokens=2048,
            )
            if not content:
                return []

            data = self._parse_yaml_block(content)
            if data and "角色表" in data:
                return data["角色表"]

        except Exception as e:
            print(f"角色提取失败: {e}")

        return []

    def _format_characters(self, characters: list[dict]) -> str:
        """将角色表格式化为上下文文本"""
        if not characters:
            return "（暂未识别到角色）"
        lines = []
        for c in characters:
            name = c.get("角色名", "未知")
            intro = c.get("角色简介", "")
            trait = c.get("性格特征", "")
            parts = [f"  - {name}"]
            if trait:
                parts.append(f"性格: {trait}")
            if intro:
                parts.append(f"简介: {intro}")
            lines.append("，".join(parts))
        return "\n".join(lines)

    # -------------------------------------------------------
    # 阶段2：逐章转换
    # -------------------------------------------------------

    def _convert_chapter_with_context(
        self, chapter_text: str, chapter_num: int, char_context: str
    ) -> dict:
        """带角色上下文的单章转换"""
        if not chapter_text.strip():
            return self._mock_act(chapter_num)

        try:
            system = CONVERTER_PROMPT.format(
                character_context=char_context,
                chapter_num=chapter_num,
            )
            user_msg = (
                f"请将以下第 {chapter_num} 章小说内容转换为剧本格式：\n\n"
                f"{chapter_text[:Config.MAX_CHAPTER_CHARS]}"
            )

            content = self._call_llm(system=system, user=user_msg, max_tokens=4096)
            if not content:
                return self._mock_act(chapter_num)

            data = self._parse_yaml_block(content)
            if data and "幕" in data:
                acts = data["幕"]
                if acts:
                    return acts[0]

        except Exception as e:
            print(f"章节 {chapter_num} 转换失败: {e}")

        return self._mock_act(chapter_num)

    # -------------------------------------------------------
    # 工具方法
    # -------------------------------------------------------

    def _parse_yaml_block(self, text: str) -> dict | None:
        """从 LLM 响应中提取并解析 YAML 块"""
        if "```yaml" in text:
            text = text.split("```yaml")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            return None

    def _split_chapters(self, text: str) -> list[str]:
        """将小说文本按章节分割"""
        patterns = [
            r"第[一二三四五六七八九十百千零\d]+[章回节]",
            r"Chapter\s+\d+",
            r"第\d+章",
            r"^\d+[\.、]",
        ]

        for pat in patterns:
            parts = re.split(pat, text, flags=re.MULTILINE)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 3:
                return parts

        # 无章节标记时按段落均分
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) >= 9:
            chunk_size = max(1, len(paragraphs) // 3)
            return [
                "\n\n".join(paragraphs[i:i + chunk_size])
                for i in range(0, len(paragraphs), chunk_size)
            ]
        return [text]

    def _consolidate_characters(
        self, result: dict, initial_chars: list[dict]
    ) -> None:
        """合并初始角色表和各幕中出现的角色，确保完整"""
        seen_names = {c.get("角色名") for c in initial_chars}
        known = {c.get("角色名"): c for c in initial_chars}

        for act in result["剧本"]["幕"]:
            for scene in act.get("场", []):
                for char_name in scene.get("人物", []):
                    if char_name and char_name not in seen_names:
                        seen_names.add(char_name)
                        known[char_name] = {
                            "角色名": char_name,
                            "年龄": "未知",
                            "性别": "未知",
                            "性格特征": "",
                            "角色简介": "",
                        }

        result["剧本"]["角色表"] = list(known.values())

    # -------------------------------------------------------
    # Mock 方法（无 API Key 时用）
    # -------------------------------------------------------

    def _mock_conversion(
        self, chapters: list[str], base: dict
    ) -> dict[str, Any]:
        for i in range(min(len(chapters), 3)):
            base["剧本"]["幕"].append(self._mock_act(i + 1))
        return base

    def _mock_act(self, num: int) -> dict:
        return {
            "幕号": num,
            "幕标题": f"第{num}幕",
            "场": [
                {
                    "场号": 1,
                    "场景": "示例场景",
                    "时间": "日",
                    "人物": ["角色甲", "角色乙"],
                    "内容": [
                        {"类型": "动作描写", "内容": "（此处为小说叙述内容的剧本化呈现）"},
                        {"类型": "对白", "角色": "角色甲", "台词": "（对话内容将在此显示）", "表情": "平静"},
                        {"类型": "舞台指示", "内容": "（舞台效果说明）"},
                    ],
                }
            ],
        }


# 单例
converter = NovelConverter()
