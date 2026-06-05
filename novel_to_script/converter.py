"""
核心转换逻辑

使用 LLM（默认 Claude API）将小说文本转换为结构化剧本 YAML。
支持分章处理、长文本分块、角色一致性等。
"""

import uuid
import yaml
from datetime import datetime
from typing import Any

from config import Config
from novel_to_script.schema import get_empty_script

# -----------------------------------------------------------
# 系统提示词
# -----------------------------------------------------------
SYSTEM_PROMPT = """你是一位专业的剧本改编专家。你的任务是将小说章节转换为结构化的剧本格式。

请严格按照以下 YAML Schema 输出：

```yaml
剧本:
  元数据:
    标题: <剧本标题>
    原作: <原作小说名称>
    原作者: <作者名>
    改编章节数: <数字>
    转换日期: <转换日期>

  角色表:
    - 角色名: <角色名>
      年龄: <年龄或"未知">
      性别: <性别>
      性格特征: <性格描述>
      角色简介: <角色背景和定位>

  幕:
    - 幕号: <数字>
      幕标题: <幕的标题>
      场:
        - 场号: <数字>
          场景: <地点/场景名>
          时间: <时间描述>
          人物: [<出现的角色名列表>]
          内容:
            - 类型: 对白
              角色: <角色名>
              台词: <对话内容>
              表情: <表情或动作指示>
            - 类型: 动作描写
              内容: <动作/叙事描述>
            - 类型: 舞台指示
              内容: <舞台/灯光/音效指示>
```

规则：
1. 小说中的叙述性文字转为「动作描写」
2. 对话直接转为「对白」，标注角色和表情
3. 场景转换处插入「舞台指示」
4. 每章至少分为 2-3 场
5. 角色表需包含所有出现的人物
6. 只输出 YAML，不要额外说明
"""


class NovelConverter:
    """小说→剧本转换器"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.client = None
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except Exception:
                self.client = None

    # -------------------------------------------------------
    # 公开接口
    # -------------------------------------------------------

    def convert(self, novel_text: str, title: str = "") -> dict[str, Any]:
        """
        将整部小说（多章节）转换为剧本结构。

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
            # 无 API Key 时返回模拟结果
            return self._mock_conversion(chapters, result)

        # 有 API Key 时调用 LLM
        for i, chapter in enumerate(chapters):
            act_data = self._convert_chapter(chapter, i + 1)
            result["剧本"]["幕"].append(act_data)

        # 合并所有幕的角色表
        all_chars = {}
        for act in result["剧本"]["幕"]:
            for scene in act.get("场", []):
                for char_name in scene.get("人物", []):
                    if char_name not in all_chars:
                        all_chars[char_name] = {
                            "角色名": char_name,
                            "年龄": "未知",
                            "性别": "未知",
                            "性格特征": "",
                            "角色简介": "",
                        }
        result["剧本"]["角色表"] = list(all_chars.values())

        return result

    # -------------------------------------------------------
    # 内部方法
    # -------------------------------------------------------

    def _split_chapters(self, text: str) -> list[str]:
        """将小说文本按章节分割"""
        import re

        # 常见的章节标记
        patterns = [
            r"第[一二三四五六七八九十百千零\d]+[章回节]",
            r"Chapter\s+\d+",
            r"第\d+章",
            r"^\d+[\.、]",
        ]

        # 尝试按章节标记分割
        for pat in patterns:
            parts = re.split(pat, text, flags=re.MULTILINE)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 3:
                return parts

        # 如果没有显式章节标记，按段落数均分（每约50段为一章）
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) >= 9:
            chunk_size = max(1, len(paragraphs) // 3)
            return [
                "\n\n".join(paragraphs[i:i + chunk_size])
                for i in range(0, len(paragraphs), chunk_size)
            ]

        # 不够分就整体当作一章
        return [text]

    def _convert_chapter(self, chapter_text: str, chapter_num: int) -> dict:
        """调用 LLM 转换单章为一场"""
        if not self.client or not chapter_text.strip():
            return self._mock_act(chapter_num)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"请将以下第 {chapter_num} 章小说内容转换为剧本格式：\n\n"
                            f"{chapter_text[:Config.MAX_CHAPTER_CHARS]}"
                        ),
                    }
                ],
            )

            content = response.content[0].text
            # 提取 YAML 块
            if "```yaml" in content:
                content = content.split("```yaml")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = yaml.safe_load(content)
            if data and "剧本" in data:
                acts = data["剧本"].get("幕", [])
                if acts:
                    return acts[0]

        except Exception as e:
            print(f"章节 {chapter_num} 转换失败: {e}")

        return self._mock_act(chapter_num)

    # -------------------------------------------------------
    # Mock 方法（无 API Key 时用）
    # -------------------------------------------------------

    def _mock_conversion(
        self, chapters: list[str], base: dict
    ) -> dict[str, Any]:
        """无 API 时的模拟转换（展示数据结构用）"""
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
                        {
                            "类型": "动作描写",
                            "内容": "（此处为小说叙述内容的剧本化呈现）",
                        },
                        {
                            "类型": "对白",
                            "角色": "角色甲",
                            "台词": "（对话内容将在此显示）",
                            "表情": "平静",
                        },
                        {
                            "类型": "舞台指示",
                            "内容": "（舞台效果说明）",
                        },
                    ],
                }
            ],
        }


# 单例
converter = NovelConverter()
