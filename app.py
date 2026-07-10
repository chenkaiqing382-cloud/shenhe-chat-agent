import base64
from pathlib import Path

import streamlit as st
from agent.core import AgentCore

st.set_page_config(
    page_title="申鹤 — 孤辰孑遗",
    page_icon="❄️",
    layout="wide",
)

BASE_DIR = Path(__file__).parent
HERO_IMAGE = BASE_DIR / "assets" / "hero-bg.png"


def _asset_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def apply_theme():
    """Public-facing visual layer for the Streamlit app."""
    hero_uri = _asset_data_uri(HERO_IMAGE)
    st.markdown(
        f"""
        <style>
        :root {{
            --ink: #0e1820;
            --muted: #5d7180;
            --mist: #eef7f8;
            --frost: #d9edf1;
            --ice: #78b9c8;
            --cord: #a6443d;
            --paper: rgba(255, 255, 255, 0.82);
            --line: rgba(67, 105, 119, 0.18);
        }}

        .stApp {{
            background:
                linear-gradient(180deg, rgba(247, 252, 252, 0.9), rgba(232, 243, 245, 0.94)),
                radial-gradient(circle at top left, rgba(166, 68, 61, 0.12), transparent 30%),
                #eef7f8;
            color: var(--ink);
        }}

        .block-container {{
            max-width: 1180px;
            padding-top: 1.4rem;
            padding-bottom: 7rem;
        }}

        section[data-testid="stSidebar"] {{
            background: rgba(246, 251, 252, 0.92);
            border-right: 1px solid var(--line);
        }}

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label {{
            color: #304752;
        }}

        h1, h2, h3 {{
            letter-spacing: 0;
            color: var(--ink);
        }}

        .shenhe-hero {{
            min-height: 330px;
            border: 1px solid rgba(255, 255, 255, 0.64);
            border-radius: 10px;
            overflow: hidden;
            position: relative;
            background-image:
                linear-gradient(90deg, rgba(8, 21, 28, 0.76) 0%, rgba(8, 21, 28, 0.48) 42%, rgba(8, 21, 28, 0.12) 100%),
                url("{hero_uri}");
            background-size: cover;
            background-position: center;
            box-shadow: 0 22px 60px rgba(33, 73, 87, 0.18);
        }}

        .shenhe-hero__content {{
            width: min(680px, 92%);
            padding: clamp(28px, 5vw, 58px);
            position: relative;
            z-index: 1;
        }}

        .shenhe-kicker {{
            color: #cfeaf0;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }}

        .shenhe-title {{
            color: #f8ffff;
            font-size: clamp(2.45rem, 7vw, 5.4rem);
            line-height: 0.98;
            font-weight: 760;
            margin: 0 0 1rem;
            text-shadow: 0 8px 30px rgba(0, 0, 0, 0.24);
        }}

        .shenhe-subtitle {{
            color: rgba(243, 253, 255, 0.9);
            font-size: clamp(1rem, 2vw, 1.18rem);
            line-height: 1.85;
            max-width: 620px;
            margin: 0 0 1.6rem;
        }}

        .shenhe-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .shenhe-pill {{
            border: 1px solid rgba(232, 250, 255, 0.34);
            color: #ecfbff;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 999px;
            padding: 8px 12px;
            font-size: 0.88rem;
            backdrop-filter: blur(8px);
        }}

        .shenhe-band {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 18px 0 20px;
        }}

        .shenhe-stat {{
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--paper);
            padding: 16px 18px;
            min-height: 96px;
        }}

        .shenhe-stat strong {{
            display: block;
            font-size: 1rem;
            color: var(--ink);
            margin-bottom: 8px;
        }}

        .shenhe-stat span {{
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.65;
        }}

        .section-label {{
            margin: 28px 0 10px;
            color: var(--cord);
            font-weight: 760;
            letter-spacing: 0.08em;
            font-size: 0.82rem;
            text-transform: uppercase;
        }}

        div[data-testid="stChatMessage"] {{
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 10px 28px rgba(28, 67, 80, 0.08);
        }}

        div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {{
            background: rgba(244, 251, 252, 0.94);
        }}

        .stButton > button {{
            border-radius: 8px;
            border: 1px solid rgba(80, 128, 142, 0.26);
            background: rgba(255, 255, 255, 0.84);
            color: #18313c;
        }}

        .stButton > button:hover {{
            border-color: rgba(166, 68, 61, 0.56);
            color: #7c2925;
        }}

        [data-testid="stChatInput"] {{
            border-top: 1px solid var(--line);
            background: rgba(241, 249, 250, 0.88);
        }}

        @media (max-width: 780px) {{
            .shenhe-hero {{
                min-height: 380px;
            }}
            .shenhe-band {{
                grid-template-columns: 1fr;
            }}
            .shenhe-hero__content {{
                padding: 30px 22px;
            }}
        }}
        </style>
        <script>
        window.setTimeout(() => {{
            const containers = window.parent.document.querySelectorAll(
                'section.main, [data-testid="stAppViewContainer"], .stApp'
            );
            containers.forEach((node) => {{
                if (node && typeof node.scrollTo === 'function') node.scrollTo(0, 0);
            }});
        }}, 80);
        </script>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def get_agent() -> AgentCore:
    return AgentCore()


def render_hero():
    st.markdown(
        """
        <section class="shenhe-hero">
            <div class="shenhe-hero__content">
                <div class="shenhe-kicker">Public AI Companion · Streamlit Cloud Ready</div>
                <div class="shenhe-title">申鹤 · 孤辰孑遗</div>
                <p class="shenhe-subtitle">
                    一个具备长期记忆、情绪状态、图片联想与语音回应能力的中文角色聊天智能体。
                    她会记住与你有关的片段，也会在每一次对话里逐渐显露心境。
                </p>
                <div class="shenhe-pills">
                    <span class="shenhe-pill">情绪驱动回应</span>
                    <span class="shenhe-pill">长期记忆</span>
                    <span class="shenhe-pill">语音生成</span>
                    <span class="shenhe-pill">公网可访问</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_feature_band(agent: AgentCore):
    mood_display = {
        "detached": "淡漠",
        "bloodlust": "杀性涌动",
        "softened": "冰霜消融",
        "melancholy": "沉郁",
    }
    facts = agent.get_facts(limit=99)
    st.markdown(
        f"""
        <div class="shenhe-band">
            <div class="shenhe-stat">
                <strong>当前心境</strong>
                <span>{mood_display.get(agent.get_mood(), "淡漠")}，会随你的话语细微改变。</span>
            </div>
            <div class="shenhe-stat">
                <strong>记忆片段</strong>
                <span>已沉淀 {len(facts)} 条与你有关的信息，用于后续对话。</span>
            </div>
            <div class="shenhe-stat">
                <strong>交互能力</strong>
                <span>支持文字对话、图片提示解析与语音回应。</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_starter_prompts():
    st.markdown('<div class="section-label">Start</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    starters = [
        "你今日为何显得如此疏离？",
        "陪我在山间走一段吧。",
        "你还记得我上次说过什么吗？",
    ]
    for col, starter in zip(cols, starters):
        if col.button(starter, use_container_width=True):
            st.session_state.pending_prompt = starter
            st.rerun()


def render_sidebar(agent: AgentCore):
    """侧边栏：情绪指示器 + 记忆 + 对话管理。"""
    with st.sidebar:
        st.title("❄️ 申鹤")
        st.caption("公网展示版")

        # ── 情绪状态 ──
        st.subheader("🔮 心境")
        emotions = agent.get_emotions()
        mood = agent.get_mood()

        mood_display = {
            "detached": "🪨 淡漠",
            "bloodlust": "⚔️ 杀性涌动",
            "softened": "🫧 冰霜消融",
            "melancholy": "🌫️ 沉郁",
        }
        st.caption(f"当前：{mood_display.get(mood, '🪨 淡漠')}")

        labels = {
            "warmth": "🔥 温度",
            "sorrow": "💧 悲意",
            "curiosity": "❓ 疑惑",
            "calmness": "🪢 红绳压制",
            "bloodlust": "⚔️ 杀性",
            "attachment": "💫 依恋",
        }
        for name, value in emotions.items():
            st.progress(value, text=f"{labels.get(name, name)} {value:.2f}")

        st.divider()

        # ── 已知信息 ──
        st.subheader("📜 对你的了解")
        facts = agent.get_facts(limit=8)
        if facts:
            for f in facts:
                st.caption(f"• {f['content']}")
        else:
            st.caption("（尚未了解你）")

        st.divider()

        # ── 对话管理 ──
        st.subheader("💬 对话")
        if st.button("🆕 新的相遇", use_container_width=True):
            agent.new_conversation()
            st.session_state.messages = []
            st.rerun()

        conversations = agent.get_conversations()
        if len(conversations) > 1:
            st.caption("过往对话：")
            for conv in conversations:
                is_current = conv["id"] == agent.conversation_id
                label = f"{'❄️' if is_current else '  '} {conv['title'][:20]}"
                if not is_current and st.button(label, key=conv["id"], use_container_width=True):
                    agent.switch_conversation(conv["id"])
                    st.session_state.messages = []
                    st.rerun()


def main():
    apply_theme()
    agent = get_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    render_sidebar(agent)
    render_hero()
    render_feature_band(agent)
    render_starter_prompts()

    # ── 主聊天区域 ──
    st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)
    st.caption("「我名申鹤，命格孤煞，易伤身边人。若不畏惧与我同行……就请伸出手来吧。」")

    # 显示历史消息
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "❄️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("image"):
                st.image(msg["image"])
            if msg.get("audio"):
                st.audio(msg["audio"])

    # 输入框
    prompt = st.session_state.pending_prompt or st.chat_input("和申鹤说话……")
    st.session_state.pending_prompt = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt, "image": None, "audio": None})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="❄️"):
            with st.spinner("申鹤正在凝神……"):
                response = agent.process_message(prompt)
            st.markdown(response["text"])
            if response.get("image_path"):
                st.image(response["image_path"])
            if response.get("audio_path"):
                st.audio(response["audio_path"])

        st.session_state.messages.append({
            "role": "assistant",
            "content": response["text"],
            "image": response.get("image_path"),
            "audio": response.get("audio_path"),
        })
        st.rerun()


if __name__ == "__main__":
    main()
