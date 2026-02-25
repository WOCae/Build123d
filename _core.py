"""
_core.py ── 状態管理 / システムプロンプト / コード実行 / API呼び出し
"""
import ast, os, re, sys, textwrap, traceback, subprocess, importlib

# ── 依存ライブラリの自動インストール ────────────────────────
def ensure_deps():
    pkgs = {'ipywidgets': 'ipywidgets', 'anthropic': 'anthropic',
            'openai': 'openai', 'google.genai': 'google-genai'}
    restart = False
    for mod, pkg in pkgs.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], check=True)
            restart = True
    if restart:
        try:
            from google.colab import runtime
            print('🔄 ライブラリをインストールしました。再起動後にもう一度実行してください。')
            runtime.unassign()
        except ImportError:
            print('✅ ライブラリインストール完了')

# ── 状態管理 ────────────────────────────────────────────────
state = dict(
    provider        = 'anthropic',
    anthropic_key   = '', openai_key   = '', google_key   = '',
    anthropic_model = 'claude-opus-4-6',
    openai_model    = 'gpt-4o',
    google_model    = 'gemini-2.5-flash',
    history = [], last_code = '', last_err = '', last_raw = '',
)

# ── システムプロンプト ────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""\
    あなたはBuild123dのエキスパートです。以下のルールに従ってPythonコードを生成してください。

    【ルール】
    1. 必ず `from build123d import *` でインポートする
    2. 形状は `with BuildPart() as part:` のコンテキストマネージャ内に書く
    3. 寸法はすべてmm単位で書く
    4. パラメータは冒頭に変数としてまとめる
    5. ブーリアン: mode=Mode.SUBTRACT（穴）/ mode=Mode.ADD（合体）
    6. BuildSketch はネストしない
    7. fillet は形状確定後、最後にグローバル関数で呼ぶ
    8. 最後に必ずこの2行:
       export_step(part.part, "output/llm_output.step")
       export_stl(part.part,  "output/llm_output.stl")
    9. 【最重要】コードブロック(```python...```)のみ返す。説明文不要。

    【fillet の正しい書き方】
    fillet(part.edges(), radius=5)   # ✅ グローバル関数・part.edges() を渡す
    # part.fillet(...)  ← ❌ メソッドは存在しない

    【禁止】filter_by_orientation / filter_by_axis は存在しない
    【代替】特定エッジ: filter_by_position(Axis.Z, min, max)
""")

BANNED = ['os.system', 'subprocess', 'eval(', 'exec(', '__import__', 'shutil.', 'requests.', 'urllib']

# ── コード処理ユーティリティ ─────────────────────────────────
def extract_code(text: str) -> str:
    m = re.search(r'```(?:python)?[ \t]*\n(.*?)```', text, re.DOTALL)
    if m: return m.group(1).strip()
    m = re.search(r'(from build123d import.*)', text, re.DOTALL)
    return m.group(1).strip() if m else ''

def validate_code_block(code: str, raw: str) -> tuple:
    if not code:
        return False, f'LLMがコードブロックを返しませんでした。\n先頭200文字:\n{raw[:200]}'
    if 'from build123d' not in code and 'BuildPart' not in code:
        return False, f'Build123dのコードが含まれていません。\n先頭200文字:\n{code[:200]}'
    return True, ''

def auto_patch(code: str) -> tuple:
    """LLMがよく間違えるパターンを自動修正"""
    patches = []
    def fix(kind, m):
        v, a = m.group(1), m.group(2)
        patches.append(f'  {v}.{kind}({a}) → {kind}({v}.edges(), {a})')
        return f'{kind}({v}.edges(), {a})'
    code = re.sub(r'(\w+)\.fillet\(([^)]+)\)',  lambda m: fix('fillet',  m), code)
    code = re.sub(r'(\w+)\.chamfer\(([^)]+)\)', lambda m: fix('chamfer', m), code)
    code = re.sub(r'(fillet|chamfer)\((\w+)\.part\.edges\(\)', r'\1(\2.edges()', code)
    for bad in ['.filter_by_orientation', '.filter_by_axis', '.filter_by_type']:
        if bad in code:
            code = re.sub(re.escape(bad) + r'\([^)]*\)', '', code)
            patches.append(f'  {bad}(...) → 削除')
    return code, patches

def run_code(code: str) -> tuple:
    code, patches = auto_patch(code)
    if patches:
        print('🔧 自動修正:')
        for p in patches: print(p)
    if bads := [b for b in BANNED if b in code]:
        return False, f'安全チェックNG: {bads}'
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f'構文エラー: {e}'
    try:
        exec(compile(code, '<generated>', 'exec'), {'__builtins__': __builtins__})
        return True, ''
    except Exception:
        return False, traceback.format_exc()

# ── API 呼び出し ─────────────────────────────────────────────
def call_api(user_msg: str, history: list) -> str:
    msgs = list(history) + [{'role': 'user', 'content': user_msg}]
    p = state['provider']

    if p == 'anthropic':
        import anthropic
        r = anthropic.Anthropic(api_key=state['anthropic_key']).messages.create(
            model=state['anthropic_model'], max_tokens=4096,
            system=SYSTEM_PROMPT, messages=msgs)
        return r.content[0].text

    elif p == 'openai':
        from openai import OpenAI
        r = OpenAI(api_key=state['openai_key']).chat.completions.create(
            model=state['openai_model'], max_tokens=4096,
            messages=[{'role': 'system', 'content': SYSTEM_PROMPT}] + msgs)
        return r.choices[0].message.content

    elif p == 'google':
        import time
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
        c = genai.Client(api_key=state['google_key'])
        gc = [types.Content(role='user' if m['role']=='user' else 'model',
                            parts=[types.Part(text=m['content'])]) for m in msgs[:-1]]
        contents = gc + [types.Content(role='user', parts=[types.Part(text=user_msg)])]
        for wait in [0, 15, 30]:
            if wait: time.sleep(wait)
            try:
                return c.models.generate_content(
                    model=state['google_model'], contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT, max_output_tokens=4096)).text
            except APIError as e:
                if e.code != 429 or wait >= 30: raise
    raise ValueError('プロバイダーが未設定です')

def test_connection(provider: str) -> tuple:
    try:
        if provider == 'anthropic':
            import anthropic
            anthropic.Anthropic(api_key=state['anthropic_key']).messages.create(
                model=state['anthropic_model'], max_tokens=8,
                messages=[{'role':'user','content':'hi'}])
        elif provider == 'openai':
            from openai import OpenAI
            OpenAI(api_key=state['openai_key']).chat.completions.create(
                model=state['openai_model'], max_tokens=8,
                messages=[{'role':'user','content':'hi'}])
        elif provider == 'google':
            from google import genai
            from google.genai import types
            genai.Client(api_key=state['google_key']).models.generate_content(
                model=state['google_model'], contents='hi',
                config=types.GenerateContentConfig(max_output_tokens=8))
        return True, '接続OK'
    except Exception as e:
        return False, str(e)[:120]
