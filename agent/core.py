import config
from agent.llm import LLMClient
from agent.personality import PersonalityEngine
from agent.memory import MemoryStore
from agent.prompts import build_system_prompt
from agent.multimodal import parse_image_request, generate_image, generate_voice


class AgentCore:
    """Nova 的核心大脑 — 编排记忆、情感、LLM、多模态。"""

    def __init__(self):
        self.client = LLMClient()
        self.personality = PersonalityEngine()
        self.memory = MemoryStore()
        self.conversation_id = self.memory.create_conversation()

    def process_message(self, user_message: str) -> dict:
        """处理一条用户消息，返回 {text, image_path, audio_path}。"""
        # 1. 存储用户消息
        self.memory.add_message(self.conversation_id, "user", user_message)

        # 2. 情绪反应
        self.personality.react_to_message(user_message)
        self.personality.decay_emotions()

        # 3. 检索相关事实
        relevant_facts = self.memory.search_facts(user_message)

        # 4. 获取最近对话
        recent_msgs = self.memory.get_recent_messages(self.conversation_id)

        # 5. 构建系统提示词
        system_prompt = build_system_prompt(self.personality, relevant_facts)

        # 6. 构建消息列表
        messages = []
        for msg in recent_msgs:
            messages.append({"role": msg["role"], "content": msg["content"]})
        # 把当前用户消息加进去（前面 add_message 后还没在列表里，所以要加）
        # 检查最后一条是否已经是这条用户消息
        if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})

        # 7. 调用 Claude
        try:
            response_text = self.client.complete(
                system_prompt=system_prompt,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
            )
        except Exception as e:
            clean_text = _friendly_model_error(e)
            self.memory.add_message(self.conversation_id, "assistant", clean_text)
            return {
                "text": clean_text,
                "image_path": None,
                "audio_path": None,
            }

        # 8. 解析图片请求
        clean_text, image_prompt = parse_image_request(response_text)

        # 9. 生成图片（如果有 [IMAGE: ...] 标签）
        image_path = None
        if image_prompt:
            image_path = generate_image(image_prompt)

        # 10. 生成语音
        audio_path = generate_voice(clean_text)

        # 11. 存储助手回复
        self.memory.add_message(self.conversation_id, "assistant", clean_text)

        # 12. 定期提取事实
        if self.memory.should_extract_facts(self.conversation_id):
            self.memory.extract_and_store_facts(self.conversation_id, self.client)

        return {
            "text": clean_text,
            "image_path": image_path,
            "audio_path": audio_path,
        }

    def new_conversation(self, title: str = ""):
        """开始新对话。"""
        self.conversation_id = self.memory.create_conversation(title)

    def get_emotions(self) -> dict:
        """返回当前情绪值，供 UI 展示。"""
        return dict(self.personality.emotions)

    def get_mood(self) -> str:
        """返回当前心情标签。"""
        return self.personality.get_mood()

    def get_facts(self, limit: int = 10) -> list[dict]:
        """返回已知事实列表。"""
        return self.memory.get_all_facts(limit)

    def get_conversations(self) -> list[dict]:
        """返回历史对话列表。"""
        return self.memory.list_conversations()

    def switch_conversation(self, conv_id: str):
        """切换到已有对话。"""
        self.conversation_id = conv_id

    def get_messages_for_display(self) -> list[dict]:
        """获取当前对话的所有消息，供 UI 渲染。"""
        return self.memory.get_all_messages(self.conversation_id)


def _friendly_model_error(error: Exception) -> str:
    text = str(error)
    if "invalid x-api-key" in text or "authentication_error" in text or "401" in text or "403" in text:
        return "山风暂歇，模型密钥似乎还未配置正确。请检查 Streamlit Secrets 中的模型 API key。"
    return f"山间灵息一时受阻，模型连接失败：{text[:220]}"
