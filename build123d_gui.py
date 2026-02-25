"""
build123d_gui.py
────────────────
Build123d × LLM ダッシュボード
インポートして display_dashboard() を呼ぶだけで完全なGUIが表示されます。

使い方:
    import build123d_gui
    build123d_gui.display_dashboard()
"""

import sys, os, ast, re, textwrap, traceback, subprocess, importlib

import ipywidgets as w
from IPython.display import display, HTML, clear_output

os.makedirs('output', exist_ok=True)

# ══════════════════════════════════════════════════════════════
# 依存ライブラリの自動インストール
# ══════════════════════════════════════════════════════════════
def _ensure_deps():
    pkgs = {
        'ipywidgets': 'ipywidgets',
        'anthropic':  'anthropic',
        'openai':     'openai',
        'google.genai': 'google-genai',
    }
    needs_restart = False
    for mod, pkg in pkgs.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], check=True)
            needs_restart = True

    if needs_restart:
        try:
            from google.colab import runtime
            print('🔄 ライブラリをインストールしました。ランタイムを再起動します...')
            print('   再起動後、このセルをもう一度実行してください。')
            runtime.unassign()
        except ImportError:
            print('✅ ライブラリインストール完了（ローカル環境）')

# ══════════════════════════════════════════════════════════════
# 状態管理
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# システムプロンプト
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = textwrap.dedent("""\
    あなたはBuild123dのエキスパートです。以下のルールに従ってPythonコードを生成してください。

    【ルール】
    1. 必ず `from build123d import *` でインポートする
    2. 形状は `with BuildPart() as part:` のコンテキストマネージャ内に書く
    3. 寸法はすべてmm単位のfloatまたはintで書く
    4. パラメータは変数として冒頭にまとめて定義する
    5. ブーリアン演算は mode=Mode.SUBTRACT（穴）または mode=Mode.ADD（合体）を使う
    6. BuildSketch はネストせず、mode=Mode.SUBTRACT で内穴を作る
    7. fillet はすべての形状確定後、最後に適用する
    8. 最後に必ずこの2行を含める:
       export_step(part.part, "output/llm_output.step")
       export_stl(part.part, "output/llm_output.stl")
    9. 【最重要】必ずコードブロック(```python\\n...\\n```)のみ返す。
       日本語の説明・コメントをコードブロックの外に書かない。
       返答の最初の文字は ``` でなければならない。

    【基本形状】Box / Cylinder / Sphere / Cone
    【配置】Locations / PolarLocations / GridLocations

    【fillet / chamfer の正しい書き方 ─ 最重要】
    # ✅ 正しい: グローバル関数として呼び出す
    with BuildPart() as part:
        Box(100, 100, 30)
        fillet(part.edges(), radius=5)        # part.edges() を渡す
        chamfer(part.edges(), length=3)       # chamfer も同様

    # ❌ 誤り（AttributeError になる）
    # part.fillet(...)   ← BuildPart オブジェクトにはfilletメソッドはない
    # part.part.fillet(...) ← これも不可

    【よくある間違い】
    - BuildSketchのネスト禁止
    - fillet/chamfer は必ず形状確定後にグローバル関数で呼ぶ
    - part.edges() の代わりに part.part.edges() と書かない
    - filter_by_orientation / filter_by_axis は存在しない → 使わない
    - 特定エッジだけにfilletしたい場合は filter_by_position(Axis.Z, min, max) を使う
      例: fillet(part.edges().filter_by_position(Axis.Z, 0, height), radius=3)
""")

BANNED = ['os.system','subprocess','eval(','exec(','__import__','shutil.','requests.','urllib']

# ══════════════════════════════════════════════════════════════
# コード処理ユーティリティ
# ══════════════════════════════════════════════════════════════
def extract_code(text):
    """LLMの返答からPythonコードブロックを確実に抽出する"""
    m = re.search(r'```(?:python)?[ \t]*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'(from build123d import.*)', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ''

def validate_code_block(code, raw_response):
    if not code:
        return False, (
            'LLMがコードブロックを返しませんでした。\n'
            f'LLMの返答（先頭200文字）:\n{raw_response[:200]}'
        )
    if 'from build123d' not in code and 'BuildPart' not in code:
        return False, (
            'Build123dのコードが含まれていません。\n'
            f'抽出されたテキスト（先頭200文字）:\n{code[:200]}'
        )
    return True, ''

def safety_check(code):
    return [b for b in BANNED if b in code]

def auto_patch(code):
    """LLMがよく間違えるパターンを実行前に自動修正する"""
    patches = []

    def fix_method_fillet(m):
        varname = m.group(1)
        args = m.group(2)
        patches.append(f'  {varname}.fillet({args}) → fillet({varname}.edges(), {args})')
        return f'fillet({varname}.edges(), {args})'
    code = re.sub(r'(\w+)\.fillet\(([^)]+)\)', fix_method_fillet, code)

    def fix_method_chamfer(m):
        varname = m.group(1)
        args = m.group(2)
        patches.append(f'  {varname}.chamfer({args}) → chamfer({varname}.edges(), {args})')
        return f'chamfer({varname}.edges(), {args})'
    code = re.sub(r'(\w+)\.chamfer\(([^)]+)\)', fix_method_chamfer, code)

    code = re.sub(r'fillet\((\w+)\.part\.edges\(\)', r'fillet(\1.edges()', code)
    code = re.sub(r'chamfer\((\w+)\.part\.edges\(\)', r'chamfer(\1.edges()', code)

    if '.filter_by_orientation' in code:
        code = re.sub(r'\.filter_by_orientation\([^)]*\)', '', code)
        patches.append('  .filter_by_orientation(...) → 削除（存在しないメソッド）')

    if '.filter_by_axis' in code:
        code = re.sub(r'\.filter_by_axis\([^)]*\)', '', code)
        patches.append('  .filter_by_axis(...) → 削除（存在しないメソッド）')

    if '.filter_by_type' in code:
        code = re.sub(r'\.filter_by_type\([^)]*\)', '', code)
        patches.append('  .filter_by_type(...) → 削除（すべてのエッジ対象に変更）')

    return code, patches

def run_code(code):
    code, patches = auto_patch(code)
    if patches:
        print('🔧 自動修正を適用しました:')
        for p in patches:
            print(p)

    dangers = safety_check(code)
    if dangers:
        return False, f'安全チェックNG: {dangers}'
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f'構文エラー: {e}'
    try:
        exec(compile(code, '<llm_generated>', 'exec'), {'__builtins__': __builtins__})
        return True, ''
    except Exception:
        return False, traceback.format_exc()

# ══════════════════════════════════════════════════════════════
# API 呼び出し
# ══════════════════════════════════════════════════════════════
def call_api(user_msg, history):
    msgs = list(history) + [{'role': 'user', 'content': user_msg}]
    p = state['provider']

    if p == 'anthropic':
        import anthropic
        c = anthropic.Anthropic(api_key=state['anthropic_key'])
        r = c.messages.create(model=state['anthropic_model'],
                               max_tokens=4096, system=SYSTEM_PROMPT, messages=msgs)
        return r.content[0].text

    elif p == 'openai':
        from openai import OpenAI
        c = OpenAI(api_key=state['openai_key'])
        r = c.chat.completions.create(
            model=state['openai_model'],
            messages=[{'role':'system','content':SYSTEM_PROMPT}] + msgs,
            max_tokens=4096)
        return r.choices[0].message.content

    elif p == 'google':
        import time
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
        c = genai.Client(api_key=state['google_key'])
        gc_msgs = []
        for m in msgs[:-1]:
            role = 'user' if m['role'] == 'user' else 'model'
            gc_msgs.append(types.Content(role=role, parts=[types.Part(text=m['content'])]))
        contents = gc_msgs + [types.Content(role='user', parts=[types.Part(text=user_msg)])]
        for wait in [0, 15, 30]:
            if wait:
                time.sleep(wait)
            try:
                r = c.models.generate_content(
                    model=state['google_model'],
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        max_output_tokens=4096))
                return r.text
            except APIError as e:
                if e.code == 429 and wait < 30:
                    continue
                raise
    else:
        raise ValueError('プロバイダーが未設定です')

def test_connection(provider):
    try:
        if provider == 'anthropic':
            import anthropic
            c = anthropic.Anthropic(api_key=state['anthropic_key'])
            c.messages.create(model=state['anthropic_model'],
                               max_tokens=8, messages=[{'role':'user','content':'hi'}])
        elif provider == 'openai':
            from openai import OpenAI
            c = OpenAI(api_key=state['openai_key'])
            c.chat.completions.create(model=state['openai_model'],
                                       messages=[{'role':'user','content':'hi'}], max_tokens=8)
        elif provider == 'google':
            from google import genai
            from google.genai import types
            c = genai.Client(api_key=state['google_key'])
            c.models.generate_content(
                model=state['google_model'],
                contents='hi',
                config=types.GenerateContentConfig(max_output_tokens=8))
        return True, '接続OK'
    except Exception as e:
        return False, str(e)[:120]

# ══════════════════════════════════════════════════════════════
# メインGUI構築・表示
# ══════════════════════════════════════════════════════════════
def display_dashboard():
    """完全なBuild123d × LLMダッシュボードを表示する"""
    _ensure_deps()

    # ── スタイル ──────────────────────────────────────────────
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

    # ── ⚙️ 設定タブ ───────────────────────────────────────────
    mode_toggle = w.ToggleButtons(
        options=[('🔑 API モード','api'),('📋 Manual モード','manual')],
        value='manual', description='動作モード:',
        style={'button_width':'150px','description_width':'80px'})

    provider_toggle = w.ToggleButtons(
        options=[('🟣 Anthropic','anthropic'),('🟢 OpenAI','openai'),('🔵 Google','google')],
        value='anthropic', description='プロバイダー:',
        style={'button_width':'130px','description_width':'90px'})

    # Anthropic
    ant_key   = w.Password(placeholder='sk-ant-api03-...', description='APIキー:',
                            style={'description_width':'70px'}, layout=w.Layout(width='460px'))
    ant_model = w.Dropdown(options=['claude-opus-4-6','claude-sonnet-4-6','claude-haiku-4-5-20251001'],
                            value='claude-opus-4-6', description='モデル:',
                            style={'description_width':'70px'}, layout=w.Layout(width='360px'))
    ant_test  = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    ant_stat  = w.HTML('<span class="st-idle">未テスト</span>')
    ant_box   = w.VBox([
        w.HTML('<b style="font-size:13px">🟣 Anthropic Claude</b>'),
        w.HTML('<span class="cad-tip">APIキーは <a href="https://console.anthropic.com/" target="_blank">console.anthropic.com</a> で取得できます</span>'),
        ant_key, ant_model,
        w.HBox([ant_test, ant_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    # OpenAI
    oai_key   = w.Password(placeholder='sk-...', description='APIキー:',
                            style={'description_width':'70px'}, layout=w.Layout(width='460px'))
    oai_model = w.Dropdown(options=['gpt-4o','gpt-4o-mini','gpt-4-turbo'],
                            value='gpt-4o', description='モデル:',
                            style={'description_width':'70px'}, layout=w.Layout(width='360px'))
    oai_test  = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    oai_stat  = w.HTML('<span class="st-idle">未テスト</span>')
    oai_box   = w.VBox([
        w.HTML('<b style="font-size:13px">🟢 OpenAI</b>'),
        w.HTML('<span class="cad-tip">APIキーは <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a> で取得できます</span>'),
        oai_key, oai_model,
        w.HBox([oai_test, oai_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    # Google
    goo_key   = w.Password(placeholder='AIza...', description='APIキー:',
                            style={'description_width':'70px'}, layout=w.Layout(width='460px'))
    goo_model = w.Dropdown(options=['gemini-2.5-flash','gemini-2.5-flash-lite','gemini-2.0-flash','gemini-2.0-flash-lite'],
                            value='gemini-2.5-flash', description='モデル:',
                            style={'description_width':'70px'}, layout=w.Layout(width='360px'))
    goo_test  = w.Button(description='🔌 接続テスト', layout=w.Layout(width='130px'))
    goo_stat  = w.HTML('<span class="st-idle">未テスト</span>')
    goo_box   = w.VBox([
        w.HTML('<b style="font-size:13px">🔵 Google AI Studio (Gemini)</b>'),
        w.HTML('<span class="cad-tip">APIキーは <a href="https://aistudio.google.com/app/apikey" target="_blank">aistudio.google.com</a> で取得できます（無料枠あり）</span>'),
        goo_key, goo_model,
        w.HBox([goo_test, goo_stat], layout=w.Layout(align_items='center', gap='10px')),
    ], layout=w.Layout(padding='8px 4px'))

    provider_area = w.VBox([ant_box])

    def on_provider_change(change=None):
        p = provider_toggle.value
        state['provider'] = p
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

    def on_mode_change(change=None):
        state['llm_mode'] = mode_toggle.value
        api_only_area.layout.display = 'block' if mode_toggle.value == 'api' else 'none'

    mode_toggle.observe(on_mode_change, names='value')

    settings_tab = w.VBox([
        w.HTML('<b style="font-size:14px">⚙️ 動作モード</b>'),
        mode_toggle,
        api_only_area,
    ], layout=w.Layout(padding='10px'))

    # 接続テストロジック
    def sync_keys(change=None):
        state['anthropic_key']   = ant_key.value
        state['openai_key']      = oai_key.value
        state['google_key']      = goo_key.value
        state['anthropic_model'] = ant_model.value
        state['openai_model']    = oai_model.value
        state['google_model']    = goo_model.value

    for widget in [ant_key, oai_key, goo_key, ant_model, oai_model, goo_model]:
        widget.observe(sync_keys, names='value')

    def make_test_handler(provider, key_widget, model_widget, stat_widget, test_btn):
        def handler(btn):
            state[provider + '_key']   = key_widget.value
            state[provider + '_model'] = model_widget.value
            state['provider'] = provider
            if not key_widget.value.strip():
                stat_widget.value = '<span class="st-ng">⚠️ キーを入力してください</span>'
                return
            test_btn.disabled = True
            stat_widget.value = '<span class="st-idle">テスト中...</span>'
            ok, msg = test_connection(provider)
            if ok:
                stat_widget.value = f'<span class="st-ok">✅ {msg}</span>'
            else:
                stat_widget.value = f'<span class="st-ng">❌ {msg}</span>'
            test_btn.disabled = False
        return handler

    ant_test.on_click(make_test_handler('anthropic', ant_key, ant_model, ant_stat, ant_test))
    oai_test.on_click(make_test_handler('openai',    oai_key, oai_model, oai_stat, oai_test))
    goo_test.on_click(make_test_handler('google',    goo_key, goo_model, goo_stat, goo_test))

    # ── 🤖 API 自動生成タブ ──────────────────────────────────
    request_box   = w.Textarea(placeholder='例: 外径60mm、内径40mm、長さ150mmのパイプ。両端にR3フィレットあり。',
                                layout=w.Layout(width='98%', height='88px'))
    generate_btn  = w.Button(description='🚀 生成', button_style='primary', layout=w.Layout(width='110px'))
    retry_btn     = w.Button(description='🔄 リトライ', button_style='danger',
                              layout=w.Layout(width='110px'), disabled=True)
    clear_btn     = w.Button(description='🗑️ 履歴クリア', button_style='warning', layout=w.Layout(width='120px'))
    max_retry_box = w.BoundedIntText(value=3, min=1, max=10, description='最大回数:',
                                      style={'description_width':'70px'}, layout=w.Layout(width='150px'))
    log_out  = w.Output()
    code_out = w.Output()

    def log(msg):
        with log_out:
            print(msg)

    def show_code(code):
        code_out.clear_output()
        with code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))

    # 履歴タブ（先に定義）
    history_out = w.Output()

    def refresh_history():
        history_out.clear_output()
        with history_out:
            if not state['history']:
                print('履歴なし'); return
            for i, m in enumerate(state['history']):
                role = '🧑 You' if m['role']=='user' else '🤖 LLM'
                s = m['content'][:140].replace('\n',' ')
                print(f'[{i}] {role}: {s}{"..." if len(m["content"])>140 else ""}')

    refresh_history()

    def do_generate(btn):
        sync_keys()
        state['llm_mode'] = mode_toggle.value
        req = request_box.value.strip()
        if not req:
            log('⚠️ リクエストを入力してください'); return
        if not (state['anthropic_key'] or state['openai_key'] or state['google_key']):
            log('⚠️ 設定タブでAPIキーを入力してください'); return
        generate_btn.disabled = True
        retry_btn.disabled = True
        log_out.clear_output()
        log('🤖 LLMにリクエスト送信中...')
        try:
            raw = call_api(req, state['history'])
            state['last_raw'] = raw
            code = extract_code(raw)
            valid, verr = validate_code_block(code, raw)
            if not valid:
                log(f'⚠️ コード抽出失敗:\n{verr}')
                log('💡 リトライします...')
                fix_req = ('コードブロック(```python ... ```)のみを返してください。説明文は不要です。\n'
                           '前回の返答にはコードブロックが含まれていませんでした。\n'
                           f'元のリクエスト: {req}')
                raw = call_api(fix_req, [])
                code = extract_code(raw)
                valid, verr = validate_code_block(code, raw)
                if not valid:
                    log(f'❌ 再試行後もコード抽出失敗:\n{verr}')
                    return
            state['last_code'] = code
            show_code(code)
            ok, err = run_code(code)
            state['last_err'] = err
            if ok:
                log('✅ 実行成功！ output/llm_output.step / .stl を確認してください')
                state['history'] += [{'role':'user','content':req},{'role':'assistant','content':raw}]
            else:
                log(f'❌ 実行エラー:\n{err}')
                log('💡 「リトライ」ボタンで自動修正を試みます')
                retry_btn.disabled = False
            refresh_history()
        except Exception as e:
            log(f'⛔ API呼び出しエラー: {e}')
        finally:
            generate_btn.disabled = False

    def do_retry(btn):
        sync_keys()
        if not state['last_code']:
            log('ℹ️ 先に生成を実行してください'); return
        retry_btn.disabled = True
        generate_btn.disabled = True
        cur_code = state['last_code']
        cur_err  = state['last_err']
        hist = list(state['history'])
        for n in range(1, max_retry_box.value + 1):
            log(f'🔄 リトライ {n}/{max_retry_box.value} ...')
            fix = (f'以下のコードでエラーが発生しました。修正したコードを返してください。\n\n'
                   f'【エラー】\n{cur_err}\n\n【コード】\n```python\n{cur_code}\n```')
            try:
                raw = call_api(fix, hist)
            except Exception as e:
                log(f'⛔ API エラー: {e}'); break
            cur_code = extract_code(raw)
            show_code(cur_code)
            ok, cur_err = run_code(cur_code)
            if ok:
                log(f'✅ リトライ {n} 回目で成功！')
                state['last_code'] = cur_code
                state['last_err']  = ''
                retry_btn.disabled = True
                break
            log(f'❌ まだエラー ({n}回目)')
            hist += [{'role':'user','content':fix},{'role':'assistant','content':raw}]
        else:
            log(f'⛔ {max_retry_box.value} 回試みましたが修正できませんでした')
        generate_btn.disabled = False

    def do_clear(btn):
        state['history'] = []; state['last_code'] = ''; state['last_err'] = ''
        log_out.clear_output(); code_out.clear_output()
        log('🗑️ 履歴をクリアしました')
        refresh_history()

    generate_btn.on_click(do_generate)
    retry_btn.on_click(do_retry)
    clear_btn.on_click(do_clear)

    api_tab = w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        request_box,
        w.HBox([generate_btn, retry_btn, clear_btn, max_retry_box],
                layout=w.Layout(gap='8px', align_items='center')),
        w.HTML('<b style="margin-top:6px">ログ</b>'),
        log_out,
        w.HTML('<b>生成コード</b>'),
        code_out,
    ])

    # ── 📋 Manual タブ ────────────────────────────────────────
    man_req_box    = w.Textarea(placeholder='例: 外径60mm、内径40mm、長さ150mmのパイプ。両端にR3フィレットあり。',
                                 layout=w.Layout(width='98%', height='88px'))
    gen_prompt_btn = w.Button(description='📋 プロンプト生成', button_style='info', layout=w.Layout(width='150px'))
    prompt_out     = w.Output()
    paste_box      = w.Textarea(placeholder='LLMから返ってきたコードをここに貼り付けてください...',
                                 layout=w.Layout(width='98%', height='180px'))
    run_paste_btn  = w.Button(description='▶️ 実行', button_style='success', layout=w.Layout(width='100px'))
    paste_log_out  = w.Output()

    def do_gen_prompt(btn):
        req = man_req_box.value.strip()
        if not req:
            with prompt_out:
                clear_output(); print('⚠️ リクエストを入力してください')
            return
        full = SYSTEM_PROMPT + '\n\n【作りたいもの】\n' + req
        prompt_out.clear_output()
        with prompt_out:
            display(HTML('<b>📋 以下をコピーして外部LLMに貼り付けてください：</b>'
                         f'<div class="cad-code" style="margin-top:6px">{full}</div>'))

    def do_run_paste(btn):
        code = extract_code(paste_box.value.strip())
        paste_log_out.clear_output()
        with paste_log_out:
            if not code:
                print('⚠️ コードを貼り付けてください'); return
            ok, err = run_code(code)
            if ok:
                print('✅ 実行成功！output/llm_output.step / .stl を確認してください')
            else:
                print(f'❌ エラー:\n{err}')

    gen_prompt_btn.on_click(do_gen_prompt)
    run_paste_btn.on_click(do_run_paste)

    manual_tab = w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        man_req_box, gen_prompt_btn, prompt_out,
        w.HTML('<hr><b>LLMから返ってきたコードを貼り付けて実行</b>'),
        paste_box, run_paste_btn, paste_log_out,
    ])

    # ── 📜 会話履歴タブ ───────────────────────────────────────
    hist_tab = w.VBox([w.HTML('<b>会話履歴（APIモード）</b>'), history_out])

    # ── 🔬 サンプルタブ ───────────────────────────────────────
    # ノートブックの全実行では実行されず、ボタン押下でのみ生成される
    SAMPLES = [
        {
            'id': 'basic_shapes',
            'label': '① 基本形状（Box / Cylinder / Sphere）',
            'desc': (
                '<b>Box（直方体）</b>: 幅100 × 奥行50 × 高さ30 mm<br>'
                '<b>Cylinder（円柱）</b>: 半径25 mm、高さ80 mm<br>'
                '<b>Sphere（球）</b>: 半径20 mm<br>'
                '<span class="cad-tip">build123d の最も基本的な3形状です。それぞれ独立した .step / .stl を出力します。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

# Box
with BuildPart() as box_part:
    Box(100, 50, 30)
export_step(box_part.part, 'output/sample_box.step')
export_stl(box_part.part,  'output/sample_box.stl')
print(f'✅ Box: 体積={box_part.part.volume:.1f} mm³  → output/sample_box.step / .stl')

# Cylinder
with BuildPart() as cyl_part:
    Cylinder(radius=25, height=80)
export_step(cyl_part.part, 'output/sample_cylinder.step')
export_stl(cyl_part.part,  'output/sample_cylinder.stl')
print(f'✅ Cylinder: 体積={cyl_part.part.volume:.1f} mm³  → output/sample_cylinder.step / .stl')

# Sphere
with BuildPart() as sph_part:
    Sphere(radius=20)
export_step(sph_part.part, 'output/sample_sphere.step')
export_stl(sph_part.part,  'output/sample_sphere.stl')
print(f'✅ Sphere: 体積={sph_part.part.volume:.1f} mm³  → output/sample_sphere.step / .stl')
""",
        },
        {
            'id': 'boolean_union',
            'label': '② ブーリアン合体（Union）',
            'desc': (
                'Box（60×60×20 mm）の上に Cylinder（半径15 mm、高さ40 mm）を合体させた形状。<br>'
                '<b>mode=Mode.ADD</b>（デフォルト）で自動的に合体されます。<br>'
                '<span class="cad-tip">複数の形状を同じ BuildPart コンテキスト内に置くだけで Union になります。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as union_part:
    Box(60, 60, 20)
    Cylinder(radius=15, height=40)

export_step(union_part.part, 'output/sample_union.step')
export_stl(union_part.part,  'output/sample_union.stl')
print(f'✅ Union 合体: 体積={union_part.part.volume:.1f} mm³  → output/sample_union.step / .stl')
""",
        },
        {
            'id': 'boolean_subtract',
            'label': '③ ブーリアン引き算（Subtract / 穴あき）',
            'desc': (
                'Box（80×80×30 mm）の中央に Cylinder（半径20 mm）で貫通穴を開けた形状。<br>'
                '<b>mode=Mode.SUBTRACT</b> を指定することで引き算になります。<br>'
                '<span class="cad-tip">穴・溝・切り欠きはすべてこのパターンで作れます。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as hole_part:
    Box(80, 80, 30)
    with Locations((0, 0, 0)):
        Cylinder(radius=20, height=30, mode=Mode.SUBTRACT)

export_step(hole_part.part, 'output/sample_subtract.step')
export_stl(hole_part.part,  'output/sample_subtract.stl')
print(f'✅ Subtract 穴あき: 体積={hole_part.part.volume:.1f} mm³  → output/sample_subtract.step / .stl')
""",
        },
        {
            'id': 'bolt_plate',
            'label': '④ ボルト穴パターン（GridLocations）',
            'desc': (
                'Box（100×100×15 mm）の四隅にボルト穴（φ10 mm、70 mmピッチ）を配置。<br>'
                '<b>GridLocations</b> で均等グリッドに穴を自動配置します。<br>'
                '<span class="cad-tip">PolarLocations（円周均等配置）と組み合わせると機械部品に応用できます。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as bolt_plate:
    Box(100, 100, 15)
    with GridLocations(70, 70, 2, 2):
        Cylinder(radius=5, height=15, mode=Mode.SUBTRACT)

export_step(bolt_plate.part, 'output/sample_bolt_plate.step')
export_stl(bolt_plate.part,  'output/sample_bolt_plate.stl')
print(f'✅ ボルト穴プレート: 体積={bolt_plate.part.volume:.1f} mm³  → output/sample_bolt_plate.step / .stl')
""",
        },
        {
            'id': 'fillet_chamfer',
            'label': '⑤ フィレット・面取り（fillet / chamfer）',
            'desc': (
                '<b>フィレット（R5）</b>: Box（80×60×25 mm）のすべてのエッジを丸める。<br>'
                '<b>面取り（C3）</b>: 同形状のエッジをC3で面取り。<br>'
                '<span class="cad-tip">fillet / chamfer はグローバル関数として、形状確定後に呼びます。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as fillet_part:
    Box(80, 60, 25)
    fillet(fillet_part.edges(), radius=5)
export_step(fillet_part.part, 'output/sample_fillet.step')
export_stl(fillet_part.part,  'output/sample_fillet.stl')
print(f'✅ フィレット R5: 体積={fillet_part.part.volume:.1f} mm³  → output/sample_fillet.step / .stl')

with BuildPart() as chamfer_part:
    Box(80, 60, 25)
    chamfer(chamfer_part.edges(), length=3)
export_step(chamfer_part.part, 'output/sample_chamfer.step')
export_stl(chamfer_part.part,  'output/sample_chamfer.stl')
print(f'✅ 面取り C3: 体積={chamfer_part.part.volume:.1f} mm³  → output/sample_chamfer.step / .stl')
""",
        },
        {
            'id': 'flange_shaft',
            'label': '⑥ 機械部品：フランジ付きシャフト',
            'desc': (
                'シャフト径 φ30 mm、長さ 120 mm に<br>'
                'フランジ（φ80 mm、厚さ 15 mm）を合体し、ボルト穴 4×φ10 mm（PCD φ60 mm）付き。<br>'
                'シャフト根元に R3 フィレット。<br>'
                '<span class="cad-tip">LLM が生成するコードの典型的な例です。パラメータを変えて応用できます。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

shaft_diameter   = 30
shaft_length     = 120
flange_diameter  = 80
flange_thickness = 15
bolt_hole_dia    = 10
bolt_pcd         = 60
n_bolts          = 4
fillet_r         = 3

with BuildPart() as flange_shaft:
    Cylinder(radius=shaft_diameter/2, height=shaft_length)
    with Locations((0, 0, -shaft_length/2 + flange_thickness/2)):
        Cylinder(radius=flange_diameter/2, height=flange_thickness)
    with PolarLocations(bolt_pcd/2, n_bolts):
        Cylinder(radius=bolt_hole_dia/2, height=flange_thickness, mode=Mode.SUBTRACT)
    fillet(
        flange_shaft.edges().filter_by_position(
            Axis.Z,
            -shaft_length/2 + flange_thickness,
            -shaft_length/2 + flange_thickness + 1
        ),
        radius=fillet_r
    )

export_step(flange_shaft.part, 'output/sample_flange_shaft.step')
export_stl(flange_shaft.part,  'output/sample_flange_shaft.stl')
print(f'✅ フランジ付きシャフト: 体積={flange_shaft.part.volume:.1f} mm³')
print(f'   シャフト径: {shaft_diameter}mm, 長さ: {shaft_length}mm')
print(f'   フランジ径: {flange_diameter}mm, ボルト穴: {n_bolts}×φ{bolt_hole_dia}mm')
print(f'   → output/sample_flange_shaft.step / .stl')
""",
        },
        {
            'id': 'l_bracket',
            'label': '⑦ 機械部品：Lブラケット',
            'desc': (
                '幅60 mm、高さ80 mm、奥行き50 mm、板厚8 mm の L 字ブラケット。<br>'
                '縦板と横板を Union で合体し、接合エッジに R5 フィレット。<br>'
                '<span class="cad-tip">Locations で配置した Box を Union することで L 字・T 字形状を作れます。</span>'
            ),
            'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

width     = 60
height    = 80
depth     = 50
thickness = 8

with BuildPart() as l_bracket:
    Box(thickness, width, height)
    with Locations((depth/2, 0, -height/2 + thickness/2)):
        Box(depth, width, thickness)
    fillet(l_bracket.edges().filter_by_position(Axis.X, 0, 1), radius=5)

export_step(l_bracket.part, 'output/sample_l_bracket.step')
export_stl(l_bracket.part,  'output/sample_l_bracket.stl')
print(f'✅ Lブラケット: 体積={l_bracket.part.volume:.1f} mm³')
print(f'   幅:{width}mm 高さ:{height}mm 奥行き:{depth}mm 板厚:{thickness}mm')
print(f'   → output/sample_l_bracket.step / .stl')
""",
        },
    ]

    # サンプルタブのウィジェット構築
    sample_log_out  = w.Output()
    sample_code_out = w.Output()

    def _make_sample_row(s):
        btn = w.Button(
            description='▶ 生成',
            button_style='success',
            layout=w.Layout(width='90px', height='36px'),
        )
        desc_html = w.HTML(
            f'<div style="font-size:13px; font-weight:600; margin-bottom:3px">{s["label"]}</div>'
            f'<div style="font-size:12px; line-height:1.6">{s["desc"]}</div>'
        )
        row = w.HBox(
            [btn, desc_html],
            layout=w.Layout(
                padding='10px',
                margin='4px 0',
                border='1px solid #dee2e6',
                border_radius='6px',
                align_items='flex-start',
                gap='14px',
            ),
        )

        def on_click(b, _code=s['code'], _label=s['label']):
            btn.disabled = True
            btn.description = '実行中...'
            sample_log_out.clear_output()
            sample_code_out.clear_output()
            with sample_code_out:
                display(HTML(f'<div class="cad-code">{_code}</div>'))
            with sample_log_out:
                print(f'▶ {_label}  を実行中...')
            import ast as _ast, traceback as _tb
            try:
                _ast.parse(_code)
                exec(compile(_code, '<sample>', 'exec'), {'__builtins__': __builtins__})
                with sample_log_out:
                    print('✅ 生成完了！  output/ フォルダを確認してください。')
            except Exception:
                with sample_log_out:
                    print('❌ エラー:\n' + _tb.format_exc())
            finally:
                btn.disabled = False
                btn.description = '▶ 生成'

        btn.on_click(on_click)
        return row

    sample_rows = [_make_sample_row(s) for s in SAMPLES]

    sample_tab = w.VBox([
        w.HTML(
            '<div style="font-size:13px; color:#555; margin-bottom:8px">'
            '▶ 生成 ボタンを押すとコードが表示され、STEP / STL ファイルが <code>output/</code> に保存されます。'
            '</div>'
        ),
        *sample_rows,
        w.HTML('<hr style="margin:10px 0"><b>実行ログ</b>'),
        sample_log_out,
        w.HTML('<b>実行コード</b>'),
        sample_code_out,
    ], layout=w.Layout(padding='10px'))

    # ── ダッシュボード組立 ────────────────────────────────────
    tabs = w.Tab(children=[settings_tab, api_tab, manual_tab, sample_tab, hist_tab])
    tabs.set_title(0, '⚙️ API設定')
    tabs.set_title(1, '🤖 API 自動生成')
    tabs.set_title(2, '📋 Manual')
    tabs.set_title(3, '🔬 サンプル')
    tabs.set_title(4, '📜 会話履歴')

    dashboard = w.VBox([
        w.HTML('<h3 style="margin:4px 0 8px">🔧 Build123d × LLM ダッシュボード</h3>'),
        tabs,
    ], layout=w.Layout(padding='8px'))

    display(dashboard)
    print('✅ GUI 起動完了  ─  まず「⚙️ API設定」タブでモードとキーを設定してください')
