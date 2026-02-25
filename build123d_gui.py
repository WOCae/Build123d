"""
build123d_gui.py ── Build123d × LLM ダッシュボード
────────────────────────────────────────────────────
使い方:
    import build123d_gui
    build123d_gui.display_dashboard()
"""
import os
os.makedirs('output', exist_ok=True)

import ipywidgets as w
from IPython.display import display, HTML

from _core    import ensure_deps, state, SYSTEM_PROMPT, extract_code, \
                      validate_code_block, run_code, call_api, test_connection
from _samples import build_sample_tab
from _mech    import build_mech_tab

CSS = """
<style>
.cad-log  { background:#0f1117; color:#c8ffc8; padding:12px; border-radius:6px;
            font-size:12px; white-space:pre-wrap; max-height:240px; overflow-y:auto; min-height:48px; }
.cad-code { background:#1e1e2e; color:#cdd6f4; padding:12px; border-radius:6px;
            font-size:11px; white-space:pre-wrap; max-height:300px; overflow-y:auto; }
.cad-tip  { color:#888; font-size:11px; margin-top:4px; }
.st-ok    { color:#16a34a; font-weight:600; }
.st-ng    { color:#dc2626; font-weight:600; }
.st-idle  { color:#6b7280; }
</style>
<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap' rel='stylesheet'>
"""


def _build_settings_tab() -> w.VBox:
    """⚙️ API設定タブ"""
    mode_toggle = w.ToggleButtons(
        options=[('🔑 API モード', 'api'), ('📋 Manual モード', 'manual')],
        value='manual', description='動作モード:',
        style={'button_width': '150px', 'description_width': '80px'})

    provider_toggle = w.ToggleButtons(
        options=[('🟣 Anthropic', 'anthropic'), ('🟢 OpenAI', 'openai'), ('🔵 Google', 'google')],
        value='anthropic', description='プロバイダー:',
        style={'button_width': '130px', 'description_width': '90px'})

    def _provider_box(name, placeholder, models, link_text, link_url):
        key   = w.Password(placeholder=placeholder, description='APIキー:',
                           style={'description_width': '70px'}, layout=w.Layout(width='460px'))
        model = w.Dropdown(options=models, value=models[0], description='モデル:',
                           style={'description_width': '70px'}, layout=w.Layout(width='360px'))
        test  = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
        stat  = w.HTML('<span class="st-idle">未テスト</span>')
        box   = w.VBox([
            w.HTML(f'<b style="font-size:13px">{name}</b>'),
            w.HTML(f'<span class="cad-tip">APIキーは <a href="{link_url}" target="_blank">'
                   f'{link_text}</a> で取得できます</span>'),
            key, model,
            w.HBox([test, stat], layout=w.Layout(align_items='center', gap='10px')),
        ], layout=w.Layout(padding='8px 4px'))
        return box, key, model, test, stat

    ant_box, ant_key, ant_model, ant_test, ant_stat = _provider_box(
        '🟣 Anthropic Claude', 'sk-ant-api03-...',
        ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
        'console.anthropic.com', 'https://console.anthropic.com/')

    oai_box, oai_key, oai_model, oai_test, oai_stat = _provider_box(
        '🟢 OpenAI', 'sk-...',
        ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
        'platform.openai.com', 'https://platform.openai.com/api-keys')

    goo_box, goo_key, goo_model, goo_test, goo_stat = _provider_box(
        '🔵 Google AI Studio (Gemini)', 'AIza...',
        ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.0-flash'],
        'aistudio.google.com', 'https://aistudio.google.com/app/apikey')

    provider_area = w.VBox([ant_box])

    def sync_keys(_=None):
        state.update(anthropic_key=ant_key.value, openai_key=oai_key.value,
                     google_key=goo_key.value, anthropic_model=ant_model.value,
                     openai_model=oai_model.value, google_model=goo_model.value)

    for wgt in [ant_key, oai_key, goo_key, ant_model, oai_model, goo_model]:
        wgt.observe(sync_keys, names='value')

    def on_provider(_=None):
        state['provider'] = provider_toggle.value
        provider_area.children = [
            {'anthropic': ant_box, 'openai': oai_box, 'google': goo_box}[provider_toggle.value]]

    provider_toggle.observe(on_provider, names='value')

    def make_test_handler(provider, key_wgt, model_wgt, stat_wgt, btn):
        def handler(_):
            state[f'{provider}_key']   = key_wgt.value
            state[f'{provider}_model'] = model_wgt.value
            state['provider'] = provider
            if not key_wgt.value.strip():
                stat_wgt.value = '<span class="st-ng">⚠️ キーを入力してください</span>'; return
            btn.disabled = True
            stat_wgt.value = '<span class="st-idle">テスト中...</span>'
            ok, msg = test_connection(provider)
            stat_wgt.value = (f'<span class="st-ok">✅ {msg}</span>' if ok
                              else f'<span class="st-ng">❌ {msg}</span>')
            btn.disabled = False
        return handler

    ant_test.on_click(make_test_handler('anthropic', ant_key, ant_model, ant_stat, ant_test))
    oai_test.on_click(make_test_handler('openai',    oai_key, oai_model, oai_stat, oai_test))
    goo_test.on_click(make_test_handler('google',    goo_key, goo_model, goo_stat, goo_test))

    api_only = w.VBox([
        w.HTML('<hr style="margin:8px 0"><b>プロバイダー選択</b>'),
        provider_toggle, provider_area,
    ], layout=w.Layout(display='none'))

    def on_mode(_=None):
        state['llm_mode'] = mode_toggle.value
        api_only.layout.display = 'block' if mode_toggle.value == 'api' else 'none'

    mode_toggle.observe(on_mode, names='value')

    return w.VBox([
        w.HTML('<b style="font-size:14px">⚙️ 動作モード</b>'),
        mode_toggle, api_only,
    ], layout=w.Layout(padding='10px'))


def _build_api_tab(history_out: w.Output) -> w.VBox:
    """🤖 API 自動生成タブ"""
    req_box    = w.Textarea(
        placeholder='例: 外径60mm、内径40mm、長さ150mmのパイプ。両端にR3フィレットあり。',
        layout=w.Layout(width='98%', height='88px'))
    gen_btn    = w.Button(description='🚀 生成', button_style='primary', layout=w.Layout(width='110px'))
    retry_btn  = w.Button(description='🔄 リトライ', button_style='danger',
                          layout=w.Layout(width='110px'), disabled=True)
    clear_btn  = w.Button(description='🗑️ 履歴クリア', button_style='warning', layout=w.Layout(width='120px'))
    max_retry  = w.BoundedIntText(value=3, min=1, max=10, description='最大回数:',
                                  style={'description_width': '70px'}, layout=w.Layout(width='150px'))
    log_out    = w.Output()
    code_out   = w.Output()

    def log(msg):
        with log_out: print(msg)

    def show_code(code):
        code_out.clear_output()
        with code_out: display(HTML(f'<div class="cad-code">{code}</div>'))

    def refresh_hist():
        history_out.clear_output()
        with history_out:
            if not state['history']:
                print('履歴なし'); return
            for i, m in enumerate(state['history']):
                role = '🧑 You' if m['role'] == 'user' else '🤖 LLM'
                s = m['content'][:140].replace('\n', ' ')
                print(f'[{i}] {role}: {s}{"..." if len(m["content"])>140 else ""}')

    refresh_hist()

    def do_generate(_):
        req = req_box.value.strip()
        if not req: log('⚠️ リクエストを入力してください'); return
        if not any([state['anthropic_key'], state['openai_key'], state['google_key']]):
            log('⚠️ 設定タブでAPIキーを入力してください'); return
        gen_btn.disabled = retry_btn.disabled = True
        log_out.clear_output()
        log('🤖 LLMにリクエスト送信中...')
        try:
            raw  = call_api(req, state['history'])
            state['last_raw'] = raw
            code = extract_code(raw)
            ok, err = validate_code_block(code, raw)
            if not ok:
                log(f'⚠️ コード抽出失敗、リトライします...')
                raw  = call_api(f'コードブロックのみ返してください。元のリクエスト: {req}', [])
                code = extract_code(raw)
                ok, err = validate_code_block(code, raw)
                if not ok: log(f'❌ 再試行後も失敗:\n{err}'); return
            state['last_code'] = code
            show_code(code)
            success, run_err = run_code(code)
            state['last_err'] = run_err
            if success:
                log('✅ 実行成功！ output/llm_output.step / .stl を確認してください')
                state['history'] += [{'role': 'user', 'content': req},
                                      {'role': 'assistant', 'content': raw}]
                retry_btn.disabled = True
            else:
                log(f'❌ 実行エラー:\n{run_err}')
                log('💡 「リトライ」ボタンで自動修正を試みます')
                retry_btn.disabled = False
            refresh_hist()
        except Exception as e:
            log(f'⛔ API呼び出しエラー: {e}')
        finally:
            gen_btn.disabled = False

    def do_retry(_):
        if not state['last_code']: log('ℹ️ 先に生成を実行してください'); return
        retry_btn.disabled = gen_btn.disabled = True
        code, err, hist = state['last_code'], state['last_err'], list(state['history'])
        for n in range(1, max_retry.value + 1):
            log(f'🔄 リトライ {n}/{max_retry.value} ...')
            fix = f'エラーを修正してください。\n【エラー】\n{err}\n\n【コード】\n```python\n{code}\n```'
            try:
                raw = call_api(fix, hist)
            except Exception as e:
                log(f'⛔ API エラー: {e}'); break
            code = extract_code(raw)
            show_code(code)
            success, err = run_code(code)
            if success:
                log(f'✅ {n} 回目で成功！')
                state['last_code'] = code; state['last_err'] = ''
                retry_btn.disabled = True; break
            log(f'❌ まだエラー ({n}回目)')
            hist += [{'role': 'user', 'content': fix}, {'role': 'assistant', 'content': raw}]
        else:
            log(f'⛔ {max_retry.value} 回試みましたが修正できませんでした')
        gen_btn.disabled = False

    def do_clear(_):
        state.update(history=[], last_code='', last_err='')
        log_out.clear_output(); code_out.clear_output()
        log('🗑️ 履歴をクリアしました')
        refresh_hist()

    gen_btn.on_click(do_generate)
    retry_btn.on_click(do_retry)
    clear_btn.on_click(do_clear)

    return w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        req_box,
        w.HBox([gen_btn, retry_btn, clear_btn, max_retry],
               layout=w.Layout(gap='8px', align_items='center')),
        w.HTML('<b style="margin-top:6px">ログ</b>'),
        log_out,
        w.HTML('<b>生成コード</b>'),
        code_out,
    ])


def _build_manual_tab() -> w.VBox:
    """📋 Manual タブ"""
    req_box    = w.Textarea(
        placeholder='例: 外径60mm、内径40mm、長さ150mmのパイプ。両端にR3フィレットあり。',
        layout=w.Layout(width='98%', height='88px'))
    prompt_btn = w.Button(description='📋 プロンプト生成', button_style='info', layout=w.Layout(width='150px'))
    prompt_out = w.Output()
    paste_box  = w.Textarea(placeholder='LLMから返ってきたコードをここに貼り付けてください...',
                            layout=w.Layout(width='98%', height='180px'))
    run_btn    = w.Button(description='▶️ 実行', button_style='success', layout=w.Layout(width='100px'))
    paste_log  = w.Output()

    def do_prompt(_):
        req = req_box.value.strip()
        if not req:
            with prompt_out: clear_output(); print('⚠️ リクエストを入力してください')
            return
        prompt_out.clear_output()
        with prompt_out:
            display(HTML('<b>📋 以下をコピーして外部LLMに貼り付けてください：</b>'
                         f'<div class="cad-code" style="margin-top:6px">'
                         f'{SYSTEM_PROMPT}\n\n【作りたいもの】\n{req}</div>'))

    def do_run(_):
        code = extract_code(paste_box.value.strip())
        paste_log.clear_output()
        with paste_log:
            if not code: print('⚠️ コードを貼り付けてください'); return
            ok, err = run_code(code)
            print('✅ 実行成功！output/llm_output.step / .stl を確認してください'
                  if ok else f'❌ エラー:\n{err}')

    prompt_btn.on_click(do_prompt)
    run_btn.on_click(do_run)

    return w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        req_box, prompt_btn, prompt_out,
        w.HTML('<hr><b>LLMから返ってきたコードを貼り付けて実行</b>'),
        paste_box, run_btn, paste_log,
    ])


# ── メインエントリポイント ────────────────────────────────────
def display_dashboard():
    """Build123d × LLM ダッシュボードを表示する"""
    ensure_deps()
    display(HTML(CSS))

    history_out  = w.Output()
    settings_tab = _build_settings_tab()
    api_tab      = _build_api_tab(history_out)
    manual_tab   = _build_manual_tab()
    sample_tab   = build_sample_tab()
    mech_tab     = build_mech_tab()
    hist_tab     = w.VBox([w.HTML('<b>会話履歴（APIモード）</b>'), history_out])

    tabs = w.Tab(children=[settings_tab, api_tab, manual_tab, sample_tab, mech_tab, hist_tab])
    for i, t in enumerate(['⚙️ API設定', '🤖 API 自動生成', '📋 Manual',
                            '🔬 サンプル', '🔩 機械部品', '📜 会話履歴']):
        tabs.set_title(i, t)

    display(w.VBox([
        w.HTML('<h3 style="margin:4px 0 8px">🔧 Build123d × LLM ダッシュボード</h3>'),
        tabs,
    ], layout=w.Layout(padding='8px')))
    print('✅ GUI 起動完了  ─  まず「⚙️ API設定」タブでモードとキーを設定してください')
