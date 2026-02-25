"""
gui/api/base.py
────────────────
APIクライアントの抽象基底クラス。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

class BaseApiClient(ABC):
    @abstractmethod
    def generate(self, user_msg: str, history: List[Dict]) -> str:
        ...

    def test_connection(self) -> Tuple[bool, str]:
        """
        デフォルト実装: "hi" を送って接続確認する。
        """
        try:
            result = self.generate("hi", [])
            return True, str(result)
        except Exception as e:
            return False, str(e)
