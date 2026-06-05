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

    # LLM API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # 每章最大字符数（超过则分块处理）
    MAX_CHAPTER_CHARS = 8000
