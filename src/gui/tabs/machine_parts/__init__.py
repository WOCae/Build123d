"""gui/tabs/machine_parts/__init__.py"""
import ipywidgets as w
from gui.state import AppState
from .spur_gear_panel import SpurGearPanel
from .hex_bolt_panel import HexBoltPanel
from .hex_nut_panel import HexNutPanel
from .bearing_panel import BearingPanel
from .pipe_fitting_panel import PipeFittingPanel
from .v_pulley_panel import VPulleyPanel


def create_machine_parts_tab(state: AppState) -> w.VBox:
    """機械部品タブ（アコーディオン）のウィジェットを返す。"""
    panels = [
        SpurGearPanel(),
        HexBoltPanel(),
        HexNutPanel(),
        BearingPanel(),
        PipeFittingPanel(),
        VPulleyPanel(),
    ]

    mech_log_out    = w.Output()
    mech_viewer_out = w.Output()
    mech_code_out   = w.Output()

    accordion = w.Accordion(children=[p.build_widget() for p in panels])
    for i, panel in enumerate(panels):
        accordion.set_title(i, panel.title)
    accordion.selected_index = 0

    return w.VBox([
        w.HTML('<div style="font-size:13px;color:#555;margin-bottom:8px">'
               'アコーディオンで部品を選び、パラメータを調整して ▶ 生成 ボタンを押してください。<br>'
               'STEP / STL が <code>output/</code> に保存されます。</div>'),
        accordion,
        w.HTML('<hr style="margin:10px 0"><b>実行ログ</b>'),
        mech_log_out,
        w.HTML('<b>🖥️ 3Dビューア</b>'),
        mech_viewer_out,
        w.HTML('<b>実行コード</b>'),
        mech_code_out,
    ], layout=w.Layout(padding='10px'))
