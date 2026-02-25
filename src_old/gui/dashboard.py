"""
gui/dashboard.py
────────────────
Build123d × LLM ダッシュボードのメインUI組み立て。
"""
from IPython.display import display, HTML
import ipywidgets as widgets
from gui.state import AppState
from gui.tabs import (
    create_api_settings_tab,
    create_auto_generation_tab,
    create_manual_tab,
    create_samples_tab,
    create_machine_parts_tab,
    create_history_tab
)

CSS_STYLES = """
<style>
.cad-log  { background:#0f1117; color:#c8ffc8; padding:12px;
            border-radius:6px; font-size:12px; white-space:pre-wrap;
            max-height:240px; overflow-y:auto; min-height:48px; }
.cad-code { background:#1e1e2e; color:#cdd6f4; padding:12px;
            border-radius:6px; font-size:11px; white-space:pre-wrap;
            max-height:300px; overflow-y:auto; }
.cad-tip  { color:#888; font-size:11px; margin-top:4px; }
.st-ok    { color:#16a34a; font-weight:600; }
.st-ng    { color:#dc2626; font-weight:600; }
.st-idle  { color:#6b7280; }
</style>
<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap' rel='stylesheet'>
"""

def display_dashboard() -> None:
    state = AppState()
    display(HTML(CSS_STYLES))
    settings_tab, _api_only_area = create_api_settings_tab(state)
    api_tab = create_auto_generation_tab(state)
    manual_tab = create_manual_tab()
    sample_tab = create_samples_tab()
    mech_tab = create_machine_parts_tab(state)
    hist_tab, _ = create_history_tab(state)

    tabs = widgets.Tab(children=[
        settings_tab, api_tab, manual_tab, sample_tab, mech_tab, hist_tab
    ])
    for i, title in enumerate([
        '⚙️ API設定', '🤖 API 自動生成', '📋 Manual',
        '🔬 サンプル', '🔩 機械部品', '📜 会話履歴'
    ]):
        tabs.set_title(i, title)
    display(widgets.VBox([
        widgets.HTML('<h3 style="margin:4px 0 8px">🔧 Build123d × LLM ダッシュボード</h3>'),
        tabs,
    ], layout=widgets.Layout(padding='8px')))
    print('✅ GUI 起動完了  ─  まず「⚙️ API設定」タブでモードとキーを設定してください')
