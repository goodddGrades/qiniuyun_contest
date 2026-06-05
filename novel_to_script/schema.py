"""
YAML Schema 定义与验证工具

定义了剧本的 YAML 结构规范，提供验证和默认值功能。
详细设计文档见 docs/yaml_schema.md
"""

import yaml
from typing import Any


# ============================================================
# Schema 模板
# ============================================================
#
# 剧本 YAML 的顶层结构如下（详细字段设计见 docs/yaml_schema.md）：
#
# 剧本:
#   元数据:          # 作品基本信息
#   角色表:          # 角色列表
#   幕:              # 幕 → 场 → 内容 的层级结构
#


SCHEMA_TEMPLATE = """\
剧本:
  元数据:
    标题: ""
    原作: ""
    原作者: ""
    改编章节数: 0
    转换日期: ""

  角色表: []

  幕: []
"""


def validate_script(yaml_str: str) -> list[str]:
    """
    验证剧本 YAML 是否符合 Schema 规范。

    返回：错误信息列表，空列表表示验证通过。
    """
    errors: list[str] = []
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        return [f"YAML 语法错误: {e}"]

    if not isinstance(data, dict):
        return ["根节点必须是一个对象"]

    script = data.get("剧本")
    if script is None:
        return ["缺少根字段: 剧本"]

    # 验证元数据
    meta = script.get("元数据", {})
    if not isinstance(meta, dict):
        errors.append("「元数据」必须是对象")

    for field in ["标题", "原作"]:
        if field not in meta:
            errors.append(f"元数据缺少字段: {field}")

    # 验证角色表
    characters = script.get("角色表", [])
    if not isinstance(characters, list):
        errors.append("「角色表」必须是数组")
    else:
        for i, char in enumerate(characters):
            if not isinstance(char, dict):
                errors.append(f"角色表第 {i + 1} 项必须是对象")
            elif "角色名" not in char:
                errors.append(f"角色表第 {i + 1} 项缺少字段: 角色名")

    # 验证幕结构
    acts = script.get("幕", [])
    if not isinstance(acts, list):
        errors.append("「幕」必须是数组")
    else:
        for ai, act in enumerate(acts):
            if not isinstance(act, dict):
                errors.append(f"第 {ai + 1} 幕必须是对象")
                continue
            scenes = act.get("场", [])
            if not isinstance(scenes, list):
                errors.append(f"第 {ai + 1} 幕的「场」必须是数组")
            else:
                for si, scene in enumerate(scenes):
                    if not isinstance(scene, dict):
                        errors.append(f"第 {ai + 1} 幕第 {si + 1} 场必须是对象")
                        continue
                    if "内容" not in scene:
                        errors.append(
                            f"第 {ai + 1} 幕第 {si + 1} 场缺少字段: 内容"
                        )

    return errors


def get_empty_script() -> dict[str, Any]:
    """返回一个空的剧本结构字典"""
    return {
        "剧本": {
            "元数据": {
                "标题": "",
                "原作": "",
                "原作者": "",
                "改编章节数": 0,
                "转换日期": "",
            },
            "角色表": [],
            "幕": [],
        }
    }
