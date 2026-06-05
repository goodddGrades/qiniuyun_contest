"""转换器测试"""

import yaml
from novel_to_script.converter import NovelConverter
from novel_to_script.schema import validate_script, get_empty_script


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


def test_split_chapters():
    """章节分割应正确处理中文标记"""
    converter = NovelConverter()
    text = """第1章 第一章内容
这是第一章的正文...

第2章 第二章内容
这是第二章的正文...

第3章 第三章内容
这是第三章的正文..."""
    chapters = converter._split_chapters(text)
    assert len(chapters) >= 3


def test_convert_without_api():
    """无 API Key 时应返回 mock 数据"""
    converter = NovelConverter(api_key="")
    result = converter.convert("第1章 测试\n内容\n第2章 测试\n内容\n第3章 测试\n内容")
    assert "剧本" in result
    assert len(result["剧本"]["幕"]) > 0
