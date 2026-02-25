"""
gui/tabs/manual_tab.py
────────────────
ManualタブのUI生成。
"""
from ipywidgets import VBox, Textarea, Button, Output, Label
from gui.state import SYSTEM_PROMPT

def create_manual_tab() -> VBox:
    """
    ManualタブのUIを返す。
    """
    prompt_area = Textarea(description='プロンプト:', layout={'width': '95%', 'height': '80px'})
    run_button = Button(description='実行', button_style='primary')
    output_area = Output()

    def on_run(_):
        with output_area:
            output_area.clear_output()
            prompt = prompt_area.value
            print(f"[SYSTEM_PROMPT]\n{SYSTEM_PROMPT}\n[USER]\n{prompt}")
            # 実際のコード生成・実行はここでは行わない

    run_button.on_click(on_run)

    return VBox([
        Label('Manualモード'),
        prompt_area,
        run_button,
        output_area
    ])
