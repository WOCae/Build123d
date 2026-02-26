"""
gui/tabs/machine_parts_tab.py
────────────────
機械部品タブのUI生成。
各部品パネルをアコーディオン形式で表示する。
"""
import ipywidgets as w
from gui.state import AppState
from gui.tabs.machine_parts import (
    SpurGearPanel,
    HexBoltPanel,
    HexNutPanel,
    BearingPanel,
    PipeFittingPanel,
    VPulleyPanel,
)


def create_machine_parts_tab(state: AppState) -> w.VBox:
    """機械部品タブのウィジェットを返す。"""

    panels = [
        SpurGearPanel(),
        HexBoltPanel(),
        HexNutPanel(),
        BearingPanel(),
        PipeFittingPanel(),
        VPulleyPanel(),
    ]

    # 共有の出力エリア（ログ・ビューア・コード）
    log_out    = w.Output()
    viewer_out = w.Output()
    code_out   = w.Output()

    # 各パネルに共有出力エリアをセット
    for p in panels:
        p.log_out    = log_out
        p.viewer_out = viewer_out
        p.code_out   = code_out

    # アコーディオンでパネルを格納
    accordion = w.Accordion(children=[p.build_widget() for p in panels])
    for i, p in enumerate(panels):
        accordion.set_title(i, p.title)
    # デフォルトで最初のパネルを開く
    accordion.selected_index = 0

    return w.VBox([
        w.HTML('<div style="font-size:13px;color:#555;margin-bottom:8px">'
               'パラメータを調整して ▶ 生成 ボタンを押してください。'
               'STEP/STL が <code>output/</code> に保存されます。</div>'),
        accordion,
        w.HTML('<hr style="margin:10px 0"><b>実行ログ</b>'),
        log_out,
        w.HTML('<b>🖥️ 3Dビューア</b>'),
        viewer_out,
        w.HTML('<b>実行コード</b>'),
        code_out,
    ], layout=w.Layout(padding='10px'))
