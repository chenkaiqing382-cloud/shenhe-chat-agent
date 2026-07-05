import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def _get_secret(key: str) -> str | None:
    """优先从 Streamlit Cloud secrets 读取，其次环境变量。"""
    try:
        import streamlit as st
        return st.secrets.get(key)
    except Exception:
        return os.getenv(key)


ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
STABILITY_API_KEY = _get_secret("STABILITY_API_KEY")

if not ANTHROPIC_API_KEY:
    raise RuntimeError("请在 .env 文件中设置 ANTHROPIC_API_KEY")

# Claude 模型
MODEL = "claude-sonnet-4-5"

# 输出目录 — 都放在桌面 project 文件夹
OUTPUT_DIR = BASE_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
IMAGE_DIR = OUTPUT_DIR / "images"

# 数据库
DB_PATH = str(OUTPUT_DIR / "agent_memory.db")

# 记忆参数
RECENT_MESSAGE_LIMIT = 20
FACT_EXTRACTION_INTERVAL = 10
MAX_FACTS_IN_PROMPT = 10

# 情绪参数
EMOTION_DECAY_RATE = 0.02

# TTS — edge-tts 神经网络语音
TTS_VOICE = "zh-CN-XiaoxiaoNeural"   # 晓晓 — 自然女声
TTS_RATE = "-10%"                     # 语速稍慢
TTS_PITCH = "-8Hz"                    # 降调，贴近申鹤的清冷淡漠
