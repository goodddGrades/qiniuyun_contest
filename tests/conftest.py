"""pytest 全局 fixtures"""

import pytest
import yaml
import uuid
from pathlib import Path
from app import app as flask_app

# 确保测试用临时目录
TEST_SCRIPT_DIR = Path("instance/test_scripts")
TEST_SCRIPT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def app():
    """提供测试用 Flask 应用实例"""
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app


@pytest.fixture
def client(app):
    """提供 Flask 测试客户端"""
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_script_id(client):
    """创建一个测试用剧本文件，返回 script_id"""
    script_id = uuid.uuid4().hex[:12]
    data = {
        "剧本": {
            "元数据": {"标题": "测试剧本", "原作": "测试小说", "改编章节数": 1, "转换日期": "2026-06-05"},
            "角色表": [{"角色名": "小明", "年龄": "25", "性别": "男", "性格特征": "勇敢", "角色简介": "主角"}],
            "幕": [
                {
                    "幕号": 1,
                    "幕标题": "第一幕",
                    "场": [
                        {
                            "场号": 1,
                            "场景": "公园",
                            "时间": "日",
                            "人物": ["小明"],
                            "内容": [
                                {"类型": "动作描写", "内容": "小明走在公园里"},
                                {"类型": "对白", "角色": "小明", "台词": "天气真好", "表情": "微笑"},
                            ],
                        }
                    ],
                }
            ],
        }
    }
    filepath = Path("instance/scripts") / f"{script_id}.yaml"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(yaml.dump(data, allow_unicode=True, indent=2), encoding="utf-8")
    return script_id