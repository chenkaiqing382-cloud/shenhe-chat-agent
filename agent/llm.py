import requests

import config


class LLMClient:
    """Small provider adapter for Anthropic and DeepSeek-compatible chat APIs."""

    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self._anthropic_client = None
        if self.provider == "anthropic":
            import anthropic

            self._anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def complete(self, system_prompt: str, messages: list[dict], max_tokens: int | None = None) -> str:
        if self.provider == "anthropic":
            return self._complete_anthropic(system_prompt, messages, max_tokens)
        if self.provider == "deepseek":
            return self._complete_deepseek(system_prompt, messages, max_tokens)
        raise RuntimeError(f"未知 LLM_PROVIDER：{self.provider}")

    def _complete_anthropic(self, system_prompt: str, messages: list[dict], max_tokens: int | None) -> str:
        response = self._anthropic_client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens or config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
            system=system_prompt,
            messages=messages,
        )
        text_blocks = [b for b in response.content if b.type == "text"]
        return text_blocks[0].text if text_blocks else ""

    def _complete_deepseek(self, system_prompt: str, messages: list[dict], max_tokens: int | None) -> str:
        payload_messages = messages
        if system_prompt:
            payload_messages = [{"role": "system", "content": system_prompt}, *messages]
        response = requests.post(
            config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions",
            headers={
                "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.DEEPSEEK_MODEL,
                "messages": payload_messages,
                "max_tokens": max_tokens or config.MAX_TOKENS,
                "temperature": config.TEMPERATURE,
                "stream": False,
            },
            timeout=90,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"DeepSeek 请求失败：HTTP {response.status_code} - {response.text[:300]}")
        data = response.json()
        return data["choices"][0]["message"]["content"]
