"""
gui/api/__init__.py
────────────────
APIクライアントファクトリ。
"""
from gui.state import AppState
from gui.api.base import BaseApiClient
from gui.api.anthropic_client import AnthropicClient
from gui.api.openai_client import OpenAIClient
from gui.api.google_client import GoogleClient

def get_api_client(state: AppState) -> BaseApiClient:
    """
    state.provider に応じて適切なAPIクライアントを返す。
    """
    if state.provider == 'anthropic':
        return AnthropicClient(state.anthropic_key, state.anthropic_model)
    elif state.provider == 'openai':
        return OpenAIClient(state.openai_key, state.openai_model)
    elif state.provider == 'google':
        return GoogleClient(state.google_key, state.google_model)
    else:
        raise ValueError(f"Unknown provider: {state.provider}")
