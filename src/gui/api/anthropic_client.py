"""
gui/api/anthropic_client.py
────────────────
Anthropic APIクライアント実装。
"""

from typing import List, Dict
from gui.api.base import BaseApiClient
from gui.state import SYSTEM_PROMPT

class AnthropicClient(BaseApiClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, user_msg: str, history: List[Dict]) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        messages = []
        for h in history:
            if h.get('role') == 'user':
                messages.append({"role": "user", "content": h.get('content', '')})
            elif h.get('role') == 'assistant':
                messages.append({"role": "assistant", "content": h.get('content', '')})
        messages.append({"role": "user", "content": user_msg})
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])

    def test_connection(self) -> tuple[bool, str]:
        try:
            result = self.generate("hi", [])
            return True, str(result)
        except Exception as e:
            return False, str(e)
