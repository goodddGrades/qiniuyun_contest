"""转换器与 Flask 路由测试 —— Schema 验证 + 章节分割 + Mock 转换"""

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


# ============================================================
# 单元测试 —— 长文本分块
# ============================================================


def test_long_chapter_split_preserves_content():
    """超长章节分割后内容不应被截断（截断在API层）"""
    converter = NovelConverter()
    long_text = (
        "第1章 超长章节\n"
        + "内容" * 5000
        + "\n\n第2章 正常章节\n正常内容"
        + "\n\n第3章 结尾\n结尾内容"
    )
    chapters = converter._split_chapters(long_text)
    assert len(chapters) >= 3
    assert "超长章节" in chapters[0]
    assert "内容" in chapters[0]


def test_split_chapters_chinese_numerals():
    """支持中文数字章节号"""
    converter = NovelConverter()
    text = "第一章 开始\n内容\n\n第二章 发展\n内容\n\n第三章 结尾\n内容"
    chapters = converter._split_chapters(text)
    assert len(chapters) >= 3


# ============================================================
# 单元测试 —— Mock 转换
# ============================================================


def test_convert_without_api():
    """无 API Key 时应返回 mock 数据"""
    converter = NovelConverter(api_key="")
    result = converter.convert(
        "第1章 测试\n内容\n第2章 测试\n内容\n第3章 测试\n内容"
    )
    assert "剧本" in result
    assert len(result["剧本"]["幕"]) > 0
    first_act = result["剧本"]["幕"][0]
    assert "幕号" in first_act
    assert "幕标题" in first_act
    assert "场" in first_act


def test_convert_too_few_chapters():
    """少于3章应该仍然能转换"""
    converter = NovelConverter(api_key="")
    result = converter.convert("第1章 只有一章")
    assert "剧本" in result


def test_mock_output_format():
    """Mock 输出应包含标准 YAML 结构字段"""
    converter = NovelConverter(api_key="")
    result = converter.convert(
        "第1章 A\n内容\n第2章 B\n内容\n第3章 C\n内容"
    )
    script = result["剧本"]
    assert "元数据" in script
    assert "角色表" in script
    assert "幕" in script


def test_mock_missing_title_defaults():
    """无标题时默认为"未命名作品" """
    converter = NovelConverter(api_key="")
    result = converter.convert(
        "第1章 A\n内容\n第2章 B\n内容\n第3章 C\n内容"
    )
    meta = result["剧本"]["元数据"]
    assert meta.get("标题") or meta.get("原作")