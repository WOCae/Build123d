"""
gui/api/openai_client.py
────────────────
OpenAI APIクライアント実装。
"""

from typing import List, Dict
from gui.api.base import BaseApiClient
from openai import OpenAI
from gui.state import SYSTEM_PROMPT

class OpenAIClient(BaseApiClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, user_msg: str, history: List[Dict]) -> str:
        client = OpenAI(api_key=self.api_key)
        messages_with_system = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for h in history:
            if h.get('role') in ('user', 'assistant'):
                messages_with_system.append({'role': h['role'], 'content': h.get('content', '')})
        messages_with_system.append({'role': 'user', 'content': user_msg})
        response = client.chat.completions.create(
            model=self.model,
            messages=messages_with_system,
            max_tokens=4096
        )
        return response.choices[0].message.content

    def test_connection(self) -> tuple[bool, str]:
        try:
            result = self.generate("hi", [])
            return True, str(result)
        except Exception as e:
            return False, str(e)
