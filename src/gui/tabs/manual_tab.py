"""
gui/tabs/manual_tab.py
────────────────
Manualタブ（外部LLM向けプロンプト生成 + コード貼り付け実行）のUI生成。
"""
import ipywidgets as w
from IPython.display import display, HTML, clear_output
from gui.state import SYSTEM_PROMPT
from gui.utils.code_utils import extract_code, run_code
from gui.utils.viewer import _find_latest_stl, _show_viewer

# コピーボタン用 JavaScript（クリップボードへコピー）
_COPY_BTN_JS = """
<script>
function copyPrompt_{uid}() {{
  var el = document.getElementById('prompt_text_{uid}');
  if (!el) return;
  var text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(function() {{
    var btn = document.getElementById('copy_btn_{uid}');
    var orig = btn.innerHTML;
    btn.innerHTML = '✅ コピー済み';
    btn.style.background = '#16a34a';
    setTimeout(function(){{ btn.innerHTML = orig; btn.style.background = ''; }}, 2000);
  }}).catch(function() {{
    // fallback: execCommand
    var ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    var btn = document.getElementById('copy_btn_{uid}');
    btn.innerHTML = '✅ コピー済み';
    setTimeout(function(){{ btn.innerHTML = '📋 コピー'; }}, 2000);
  }});
}}
</script>
"""

_COPY_BTN_HTML = """
<div style="position:relative">
  <button id="copy_btn_{uid}"
    onclick="copyPrompt_{uid}()"
    style="position:absolute;top:6px;right:6px;z-index:10;
           padding:4px 12px;font-size:12px;border:1px solid #aaa;
           border-radius:4px;cursor:pointer;background:#f3f4f6">
    📋 コピー
  </button>
  <pre id="prompt_text_{uid}"
    style="background:#1e1e2e;color:#cdd6f4;padding:12px 60px 12px 12px;
           border-radius:6px;font-size:11px;white-space:pre-wrap;
           max-height:300px;overflow-y:auto;margin:0">{text}</pre>
</div>
"""


def create_manual_tab() -> w.VBox:
    """Manualタブのウィジェットを返す。"""
    man_req_box = w.Textarea(
        placeholder='例: 外径60mm、内径40mm、長さ150mmのパイプ。両端にR3フィレットあり。',
        layout=w.Layout(width='98%', height='88px')
    )
    gen_prompt_btn = w.Button(
        description='📋 プロンプト生成', button_style='info',
        layout=w.Layout(width='150px')
    )
    prompt_out = w.Output()
    paste_box = w.Textarea(
        placeholder='LLMから返ってきたコードをここに貼り付けてください...',
        layout=w.Layout(width='98%', height='180px')
    )
    run_paste_btn = w.Button(
        description='▶️ 実行', button_style='success',
        layout=w.Layout(width='100px')
    )
    paste_log_out    = w.Output()
    paste_viewer_out = w.Output()
    paste_code_out   = w.Output()

    # UID でコピーボタン・テキスト要素を識別（複数タブ共存対応）
    _uid = 'manual01'

    def do_gen_prompt(btn: w.Button) -> None:
        req = man_req_box.value.strip()
        if not req:
            with prompt_out:
                clear_output()
                print('⚠️ リクエストを入力してください')
            return
        full_text = SYSTEM_PROMPT + '\n\n【作りたいもの】\n' + req
        # HTML エスケープ（<>が崩れないよう）
        import html as _html
        escaped = _html.escape(full_text)

        prompt_out.clear_output()
        with prompt_out:
            display(HTML(
                '<b>📋 以下をコピーして外部LLMに貼り付けてください：</b>'
                + _COPY_BTN_JS.format(uid=_uid)
                + _COPY_BTN_HTML.format(uid=_uid, text=escaped)
            ))

    def do_run_paste(btn: w.Button) -> None:
        code = extract_code(paste_box.value.strip())
        paste_log_out.clear_output()
        paste_viewer_out.clear_output()
        paste_code_out.clear_output()

        with paste_log_out:
            if not code:
                print('⚠️ コードを貼り付けてください')
                return
        with paste_code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))
        with paste_log_out:
            print('▶ 実行中...')

        ok, err = run_code(code)
        if ok:
            with paste_log_out:
                print('✅ 実行成功！output/llm_output.step / .stl を確認してください')
            stl = _find_latest_stl(code)
            if stl:
                _show_viewer(stl, paste_viewer_out)
        else:
            with paste_log_out:
                print(f'❌ エラー:\n{err}')

    gen_prompt_btn.on_click(do_gen_prompt)
    run_paste_btn.on_click(do_run_paste)

    return w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        man_req_box,
        gen_prompt_btn,
        prompt_out,
        w.HTML('<hr><b>LLMから返ってきたコードを貼り付けて実行</b>'),
        paste_box,
        run_paste_btn,
        w.HTML('<b>ログ</b>'),
        paste_log_out,
        w.HTML('<b>🖥️ 3Dビューア</b>'),
        paste_viewer_out,
        w.HTML('<b>実行コード</b>'),
        paste_code_out,
    ])
