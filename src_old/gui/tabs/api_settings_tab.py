"""
gui/tabs/api_settings_tab.py
────────────────
API設定タブのUI生成。
"""
from ipywidgets import VBox, HBox, Text, Dropdown, Label, Layout
from gui.state import AppState

def create_api_settings_tab(state: AppState) -> tuple[VBox, VBox]:
    """
    Returns:
        (settings_tab_widget, api_only_area)
        ※ api_only_area は auto_generation_tab 側から参照されるため両方返す
    """
    provider_dropdown = Dropdown(
        options=[('Google', 'google'), ('OpenAI', 'openai'), ('Anthropic', 'anthropic')],
        value=state.provider,
        description='プロバイダ:',
        layout=Layout(width='220px')
    )
    anthropic_key_input = Text(description='Anthropic Key:', value=state.anthropic_key, layout=Layout(width='350px'))
    openai_key_input = Text(description='OpenAI Key:', value=state.openai_key, layout=Layout(width='350px'))
    google_key_input = Text(description='Google Key:', value=state.google_key, layout=Layout(width='350px'))
    # ... 必要に応じてモデル選択や追加設定 ...
    def on_provider_change(change):
        state.provider = change['new']
    provider_dropdown.observe(on_provider_change, names='value')
    def on_anthropic_key_change(change):
        state.anthropic_key = change['new']
    anthropic_key_input.observe(on_anthropic_key_change, names='value')
    def on_openai_key_change(change):
        state.openai_key = change['new']
    openai_key_input.observe(on_openai_key_change, names='value')
    def on_google_key_change(change):
        state.google_key = change['new']
    google_key_input.observe(on_google_key_change, names='value')
    api_only_area = VBox([
        Label('APIキー設定'),
        anthropic_key_input,
        openai_key_input,
        google_key_input
    ])
    settings_tab_widget = VBox([
        Label('APIプロバイダ選択'),
        provider_dropdown,
        api_only_area
    ])
    return settings_tab_widget, api_only_area
