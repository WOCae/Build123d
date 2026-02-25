"""
gui/tabs/auto_generation_tab.py
────────────────
API自動生成タブのUI生成（ocp_cad_viewer 対応版）。
"""
import ipywidgets as w
from IPython.display import display, HTML
from gui.state import AppState
from gui.api import get_api_client
from gui.utils.code_utils import extract_code, validate_code_block, run_code
from gui.utils.viewer import _show_viewer


def create_auto_generation_tab(state: AppState) -> w.VBox:
    """API自動生成タブのウィジェットを返す。"""
    request_box  = w.Textarea(
        placeholder='例: 外径50mm・内径30mm・長さ100mmのパイプ。両端にR3フィレット。',
        layout=w.Layout(width='98%', height='88px')
    )
    generate_btn = w.Button(description='🤖 生成',      button_style='primary',
                            layout=w.Layout(width='110px'))
    retry_btn    = w.Button(description='🔄 リトライ',  button_style='danger',
                            layout=w.Layout(width='110px'), disabled=True)
    clear_btn    = w.Button(description='🗑️ 履歴クリア', button_style='warning',
                            layout=w.Layout(width='120px'))
    max_retry_box = w.BoundedIntText(
        value=3, min=1, max=10, description='最大回数:',
        style={'description_width': '70px'}, layout=w.Layout(width='150px')
    )
    log_out     = w.Output()
    code_out    = w.Output()
    viewer_out  = w.Output()

    def log(msg: str) -> None:
        with log_out:
            print(msg)

    def show_code(code: str) -> None:
        code_out.clear_output()
        with code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))

    def do_generate(btn: w.Button) -> None:
        req = request_box.value.strip()
        if not req:
            log('⚠️ リクエストを入力してください')
            return
        key = getattr(state, state.provider + '_key', '')
        if not key:
            log('⚠️ 設定タブでAPIキーを入力してください')
            return

        generate_btn.disabled = True
        retry_btn.disabled = True
        log_out.clear_output()
        code_out.clear_output()
        viewer_out.clear_output()
        log('🤖 LLMにリクエスト送信中...')

        try:
            client = get_api_client(state)
            raw = client.generate(req, state.history)
            state.last_raw = raw
            code = extract_code(raw)
            valid, verr = validate_code_block(code, raw)
            if not valid:
                log(f'⚠️ コード抽出失敗:\n{verr}')
                return

            state.last_code = code
            show_code(code)
            
            # オブジェクトを受け取るように修正
            ok, err, obj = run_code(code)
            state.last_err = err
            
            if ok:
                log('✅ 実行成功！')
                state.history += [
                    {'role': 'user',      'content': req},
                    {'role': 'assistant', 'content': raw},
                ]
                # ocp_cad_viewer で表示
                _show_viewer(obj, viewer_out)
            else:
                log(f'❌ 実行エラー:\n{err}')
                retry_btn.disabled = False
        except Exception as e:
            log(f'⛔ API呼び出しエラー: {e}')
        finally:
            generate_btn.disabled = False

    def do_retry(btn: w.Button) -> None:
        if not state.last_code:
            log('ℹ️ 先に生成を実行してください')
            return
        retry_btn.disabled = True
        generate_btn.disabled = True
        cur_code = state.last_code
        cur_err  = state.last_err
        hist = list(state.history)

        for n in range(1, max_retry_box.value + 1):
            log(f'🔄 リトライ {n}/{max_retry_box.value} ...')
            fix = (f'以下のコードでエラーが発生しました。修正したコードを返してください。\n\n'
                   f'【エラー】\n{cur_err}\n\n【コード】\n```python\n{cur_code}\n```')
            try:
                client = get_api_client(state)
                raw = client.generate(fix, hist)
            except Exception as e:
                log(f'⛔ API エラー: {e}')
                break
            cur_code = extract_code(raw)
            show_code(cur_code)
            ok, cur_err, obj = run_code(cur_code)
            if ok:
                log(f'✅ リトライ {n} 回目で成功！')
                state.last_code = cur_code
                state.last_err  = ''
                retry_btn.disabled = True
                _show_viewer(obj, viewer_out)
                break
            log(f'❌ まだエラー ({n}回目)')
            hist += [{'role': 'user', 'content': fix}, {'role': 'assistant', 'content': raw}]
        else:
            log(f'⛔ {max_retry_box.value} 回試みましたが修正できませんでした')
        generate_btn.disabled = False

    def do_clear(btn: w.Button) -> None:
        state.history = []
        state.last_code = ''
        state.last_err  = ''
        log_out.clear_output()
        code_out.clear_output()
        viewer_out.clear_output()
        log('🗑️ 履歴をクリアしました')

    generate_btn.on_click(do_generate)
    retry_btn.on_click(do_retry)
    clear_btn.on_click(do_clear)

    return w.VBox([
        w.HTML('<b>作りたいCADモデルを日本語で入力してください</b>'),
        request_box,
        w.HBox([generate_btn, retry_btn, clear_btn, max_retry_box],
               layout=w.Layout(gap='8px', align_items='center')),
        w.HTML('<b style="margin-top:6px">ログ</b>'),
        log_out,
        w.HTML('<b>🖥️ 3Dビューア (ocp_cad_viewer)</b>'),
        viewer_out,
        w.HTML('<b>生成コード</b>'),
        code_out,
    ])