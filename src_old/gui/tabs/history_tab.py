"""
gui/tabs/history_tab.py
────────────────
会話履歴タブのUI生成。
"""
from ipywidgets import VBox, Output, Button, Label
from gui.state import AppState
from typing import Callable, Tuple

def create_history_tab(state: AppState) -> Tuple[VBox, Callable]:
    """
    Returns:
        (history_tab_widget, refresh_history_fn)
        ※ refresh_history_fn は auto_generation_tab から呼び出せるよう返す
    """
    output_area = Output()
    refresh_button = Button(description='履歴更新', button_style='info')

    def refresh_history():
        with output_area:
            output_area.clear_output()
            for i, h in enumerate(state.history):
                print(f"[{i}] {h.get('role', '')}: {h.get('content', '')}")

    refresh_button.on_click(lambda _: refresh_history())
    history_tab_widget = VBox([
        Label('会話履歴'),
        refresh_button,
        output_area
    ])
    return history_tab_widget, refresh_history
