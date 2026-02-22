import sys, os, ast, re, textwrap, traceback
import ipywidgets as w
from IPython.display import display, HTML, clear_output

os.makedirs('output', exist_ok=True)

# ── 状態管理 ──
state = dict(
    llm_mode        = 'manual',
    provider        = 'anthropic',
    anthropic_key   = '',
    openai_key      = '',
    google_key      = '',
    anthropic_model = 'claude-opus-4-6',
    openai_model    = 'gpt-4o',
    google_model    = 'gemini-2.5-flash',
    history         = [],
    last_code       = '',
    last_err        = '',
    last_raw        = '',
)

# ── ダッシュボード表示関数 ──
def display_dashboard():
    display(HTML("""
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
    """))

    # 必要なウィジェットを定義
    mode_toggle = w.ToggleButtons(
        options=[('🔑 API モード','api'),('📋 Manual モード','manual')],
        value='manual', description='動作モード:',
        style={'button_width':'150px','description_width':'80px'})
    settings_tab = w.VBox([w.HTML('<b style="font-size:14px">⚙️ 動作モード</b>'), mode_toggle], layout=w.Layout(padding='10px'))
    tabs = w.Tab(children=[settings_tab])
    tabs.set_title(0, '⚙️ API設定')
    dashboard = w.VBox([
        w.HTML('<h3 style="margin:4px 0 8px">🔧 Build123d × LLM ダッシュボード</h3>'),
        tabs,
    ], layout=w.Layout(padding='8px'))
    display(dashboard)
    print('✅ GUI 起動完了  ─  まず「⚙️ API設定」タブでキーを設定してください')

# 必要に応じて他の関数や状態もこのファイルにまとめてください。
