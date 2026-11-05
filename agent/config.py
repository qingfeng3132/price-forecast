# -*- coding: utf-8 -*-
"""
第四周 · Agent 配置加载模块
从 agent/.env 读取 DeepSeek key 和后端地址（敏感信息不进 git）
"""
import os
from pathlib import Path

# agent 目录 = 本文件所在目录
AGENT_DIR = Path(__file__).resolve().parent


def load_env():
    """读取 agent/.env 到环境变量（已存在的环境变量不覆盖）"""
    env_file = AGENT_DIR / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


# 加载一次
load_env()

# 对外暴露配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
BACKEND_BASE = os.environ.get("BACKEND_BASE", "http://localhost:8080")
