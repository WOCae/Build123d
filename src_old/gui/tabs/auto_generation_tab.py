"""
gui/tabs/auto_generation_tab.py
────────────────
API自動生成タブのUI生成。
"""
from ipywidgets import VBox, Button, Output, Textarea, Label
from gui.state import AppState
from gui.api import get_api_client

def create_auto_generation_tab(state: AppState) -> VBox:
    """
    API自動生成タブのUIを返す。
    """
    prompt_input = Textarea(description='プロンプト:', layout={'width': '95%', 'height': '80px'})
    generate_button = Button(description='生成', button_style='primary')
    retry_button = Button(description='再試行', button_style='warning')
    clear_button = Button(description='クリア', button_style='info')
    output_area = Output()
    last_prompt = {'value': ''}

    def do_generate(_):
        with output_area:
            output_area.clear_output()
            prompt = prompt_input.value
            last_prompt['value'] = prompt
            try:
                client = get_api_client(state)
                result = client.generate(prompt, state.history)
                print(result)
            except Exception as e:
                print(f"[エラー] {e}")

    def do_retry(_):
        with output_area:
            output_area.clear_output()
            prompt = last_prompt['value']
            try:
                client = get_api_client(state)
                result = client.generate(prompt, state.history)
                print(result)
            except Exception as e:
                print(f"[エラー] {e}")

    def do_clear(_):
        prompt_input.value = ''
        output_area.clear_output()

    generate_button.on_click(do_generate)
    retry_button.on_click(do_retry)
    clear_button.on_click(do_clear)

    return VBox([
        Label('API自動生成'),
        prompt_input,
        generate_button,
        retry_button,
        clear_button,
        output_area
    ])
