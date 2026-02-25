"""
gui/api/google_client.py
────────────────
Google GenerativeAI APIクライアント実装。
"""

import time
from typing import List, Dict
from gui.api.base import BaseApiClient
from google import genai
from google.genai import types
from google.genai.errors import APIError
from gui.state import SYSTEM_PROMPT

class GoogleClient(BaseApiClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, user_msg: str, history: List[Dict]) -> str:
        client = genai.Client(api_key=self.api_key)
        gc_msgs = []
        for m in history:
            role = 'user' if m['role'] == 'user' else 'model'
            gc_msgs.append(types.Content(role=role, parts=[types.Part(text=m['content'])]))
        contents = gc_msgs + [types.Content(role='user', parts=[types.Part(text=user_msg)])]
        for wait in [0, 15, 30]:
            if wait:
                time.sleep(wait)
            try:
                r = client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        max_output_tokens=4096
                    )
                )
                return r.text
            except APIError as e:
                if e.code == 429 and wait < 30:
                    continue
                raise

    def test_connection(self) -> tuple[bool, str]:
        try:
            result = self.generate("hi", [])
            return True, str(result)
        except Exception as e:
            return False, str(e)
