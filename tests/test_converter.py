"""转换器与 Flask 路由测试 —— Schema 验证 + 章节分割"""

import yaml
from novel_to_script.converter import NovelConverter
from novel_to_script.schema import validate_script, get_empty_script


# ============================================================
# 单元测试 —— Schema
# ============================================================


def test_empty_script_structure():
    """空剧本结构应包含必要字段"""
    script = get_empty_script()
    assert "剧本" in script
    assert "元数据" in script["剧本"]
    assert "角色表" in script["剧本"]
    assert "幕" in script["剧本"]


def test_validate_valid_yaml():
    """有效 YAML 应通过验证"""
    valid = yaml.dump(get_empty_script(), allow_unicode=True)
    errors = validate_script(valid)
    assert errors == []


def test_validate_invalid_yaml():
    """无效 YAML 应返回错误"""
    errors = validate_script("{坏: yaml")
    assert len(errors) > 0


# ============================================================
# 单元测试 —— 章节分割
# ============================================================


def test_split_chapters_by_chinese_marker():
    """中文「第X章」标记应正确分割"""
    converter = NovelConverter()
    text = (
        "第1章 第一章内容\n"
        "这是第一章的正文...\n\n"
        "第2章 第二章内容\n"
        "这是第二章的正文...\n\n"
        "第3章 第三章内容\n"
        "这是第三章的正文..."
    )
    chapters = converter._split_chapters(text)
    assert len(chapters) >= 3


def test_split_chapters_no_marker_fallback():
    """无章节标记时自动按段落均分"""
    converter = NovelConverter()
    paragraphs = "\n\n".join([f"这是第{i}段正文内容" for i in range(1, 13)])
    chapters = converter._split_chapters(paragraphs)
    assert 3 <= len(chapters) <= 12


def test_split_chapters_short_text():
    """短文本（不足3章）应返回单个块"""
    converter = NovelConverter()
    chapters = converter._split_chapters("只有一段文字")
    assert len(chapters) == 1


def test_split_chapters_mixed_formats():
    """支持多种章节格式混合"""
    converter = NovelConverter()
    text = (
        "Chapter 1 开头\n"
        "正文内容...\n\n"
        "Chapter 2 发展\n"
        "更多内容...\n\n"
        "Chapter 3 高潮\n"
        "高潮内容..."
    )
    chapters = converter._split_chapters(text)
    assert len(chapters) >= 3