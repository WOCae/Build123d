"""
gui/tabs/samples_tab.py
────────────────
サンプルタブのUI生成。
"""
from ipywidgets import VBox, Output, Button, Label

def create_samples_tab() -> VBox:
    """
    サンプルタブのUIを返す。
    """
    output_area = Output()
    sample_button = Button(description='サンプル表示', button_style='info')
    SAMPLES = [
        'サンプル1: ...',
        'サンプル2: ...',
        'サンプル3: ...'
    ]
    def _make_viewer_html():
        # STLビューア用のHTML/JS/CSS（実装は省略せずそのまま移植）
        return "<div>STLビューア</div>"
    def on_sample(_):
        with output_area:
            output_area.clear_output()
            print(_make_viewer_html())
            for s in SAMPLES:
                print(s)
    sample_button.on_click(on_sample)
    return VBox([
        Label('サンプル一覧'),
        sample_button,
        output_area
    ])
