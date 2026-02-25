"""
gui/tabs/api_settings_tab.py
────────────────
API設定タブのUI生成。
モード切替・プロバイダー選択・APIキー入力・接続テストを含む元の画面を再現。
"""
import ipywidgets as w
from IPython.display import display, HTML
from typing import Tuple
from gui.state import AppState


def create_api_settings_tab(state: AppState) -> Tuple[w.VBox, w.VBox]:
    """
    Returns:
        (settings_tab_widget, api_only_area)
    """

    # ── モード切替 ────────────────────────────────────────────
    mode_toggle = w.ToggleButtons(
        options=[('🔑 API モード', 'api'), ('📋 Manual モード', 'manual')],
        value=state.llm_mode,
        description='動作モード:',
        style={'button_width': '150px', 'description_width': '80px'},
    )

    # ── プロバイダー選択 ──────────────────────────────────────
    provider_toggle = w.ToggleButtons(
        options=[('🔵 Google', 'google'), ('🟣 Anthropic', 'anthropic'), ('🟢 OpenAI', 'openai')],
        value=state.provider,
        description='プロバイダー:',
        style={'button_width': '130px', 'description_width': '90px'},
    )

    # ── Anthropic ────────────────────────────────────────────
    ant_key = w.Password(
        placeholder='sk-ant-api03-...', description='APIキー:',
        style={'description_width': '70px'}, layout=w.Layout(width='460px'),
        value=state.anthropic_key,
    )
    ant_model = w.Dropdown(
        options=['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
        value=state.anthropic_model, description='モデル:',
        style={'description_width': '70px'}, layout=w.Layout(width='360px'),
    )
    ant_test = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    ant_stat = w.HTML('<span class="st-idle">未テスト</span>')
    ant_box = w.VBox([
        w.HTML('<b style="font-size:13px">🟣 Anthropic Claude</b>'),
        w.HTML('<span class="cad-tip">APIキーは '
               '<a href="https://console.anthropic.com/" target="_blank">console.anthropic.com</a>'
               ' で取得できます</span>'),
        ant_key, ant_model,
        w.HBox([ant_test, ant_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    # ── OpenAI ───────────────────────────────────────────────
    oai_key = w.Password(
        placeholder='sk-...', description='APIキー:',
        style={'description_width': '70px'}, layout=w.Layout(width='460px'),
        value=state.openai_key,
    )
    oai_model = w.Dropdown(
        options=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
        value=state.openai_model, description='モデル:',
        style={'description_width': '70px'}, layout=w.Layout(width='360px'),
    )
    oai_test = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    oai_stat = w.HTML('<span class="st-idle">未テスト</span>')
    oai_box = w.VBox([
        w.HTML('<b style="font-size:13px">🟢 OpenAI</b>'),
        w.HTML('<span class="cad-tip">APIキーは '
               '<a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>'
               ' で取得できます</span>'),
        oai_key, oai_model,
        w.HBox([oai_test, oai_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    # ── Google ───────────────────────────────────────────────
    goo_key = w.Password(
        placeholder='AIza...', description='APIキー:',
        style={'description_width': '70px'}, layout=w.Layout(width='460px'),
        value=state.google_key,
    )
    goo_model = w.Dropdown(
        options=['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.0-flash', 'gemini-2.0-flash-lite'],
        value=state.google_model, description='モデル:',
        style={'description_width': '70px'}, layout=w.Layout(width='360px'),
    )
    goo_test = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    goo_stat = w.HTML('<span class="st-idle">未テスト</span>')
    goo_box = w.VBox([
        w.HTML('<b style="font-size:13px">🔵 Google AI Studio (Gemini)</b>'),
        w.HTML('<span class="cad-tip">APIキーは '
               '<a href="https://aistudio.google.com/app/apikey" target="_blank">aistudio.google.com</a>'
               ' で取得できます（無料枠あり）</span>'),
        goo_key, goo_model,
        w.HBox([goo_test, goo_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    # ── プロバイダー切替エリア ────────────────────────────────
    provider_area = w.VBox([goo_box])

    def on_provider_change(change=None) -> None:
        p = provider_toggle.value
        state.provider = p
        if p == 'anthropic':
            provider_area.children = [ant_box]
        elif p == 'openai':
            provider_area.children = [oai_box]
        else:
            provider_area.children = [goo_box]

    provider_toggle.observe(on_provider_change, names='value')

    api_only_area = w.VBox([
        w.HTML('<hr style="margin:8px 0">'),
        w.HTML('<b>プロバイダー選択</b>'),
        provider_toggle,
        provider_area,
    ], layout=w.Layout(display='none'))

    def on_mode_change(change=None) -> None:
        state.llm_mode = mode_toggle.value
        api_only_area.layout.display = 'block' if mode_toggle.value == 'api' else 'none'

    mode_toggle.observe(on_mode_change, names='value')

    # ── state 同期 ────────────────────────────────────────────
    def sync_keys(change=None) -> None:
        state.anthropic_key   = ant_key.value
        state.openai_key      = oai_key.value
        state.google_key      = goo_key.value
        state.anthropic_model = ant_model.value
        state.openai_model    = oai_model.value
        state.google_model    = goo_model.value

    for widget in [ant_key, oai_key, goo_key, ant_model, oai_model, goo_model]:
        widget.observe(sync_keys, names='value')

    # ── 接続テスト ────────────────────────────────────────────
    def make_test_handler(provider: str, key_widget, model_widget, stat_widget, test_btn):
        def handler(btn) -> None:
            state.__dict__[provider + '_key']   = key_widget.value
            state.__dict__[provider + '_model'] = model_widget.value
            state.provider = provider
            if not key_widget.value.strip():
                stat_widget.value = '<span class="st-ng">⚠️ キーを入力してください</span>'
                return
            test_btn.disabled = True
            stat_widget.value = '<span class="st-idle">テスト中...</span>'
            try:
                from gui.api import get_api_client
                sync_keys()
                client = get_api_client(state)
                ok, msg = client.test_connection()
                if ok:
                    stat_widget.value = '<span class="st-ok">✅ 接続OK</span>'
                else:
                    stat_widget.value = f'<span class="st-ng">❌ {msg[:80]}</span>'
            except Exception as e:
                stat_widget.value = f'<span class="st-ng">❌ {str(e)[:80]}</span>'
            finally:
                test_btn.disabled = False
        return handler

    ant_test.on_click(make_test_handler('anthropic', ant_key, ant_model, ant_stat, ant_test))
    oai_test.on_click(make_test_handler('openai',    oai_key, oai_model, oai_stat, oai_test))
    goo_test.on_click(make_test_handler('google',    goo_key, goo_model, goo_stat, goo_test))

    settings_tab = w.VBox([
        w.HTML('<b style="font-size:14px">⚙️ 動作モード</b>'),
        mode_toggle,
        api_only_area,
    ], layout=w.Layout(padding='10px'))

    return settings_tab, api_only_area
