"""
应用配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置类"""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 最大上传 10MB

    # LLM API — 二选一配置即可
    # 方案A：Claude（Anthropic）
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    # 方案B：DeepSeek（OpenAI 兼容接口）
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    # 自动选择：有 DEEPSEEK_API_KEY 就用 DeepSeek，否则用 Anthropic
    LLM_PROVIDER = "deepseek" if os.getenv("DEEPSEEK_API_KEY") else "anthropic"

    # 每章最大字符数（超过则分块处理）
    MAX_CHAPTER_CHARS = 8000
