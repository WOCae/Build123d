"""
gui/tabs/machine_parts/__init__.py
────────────────
機械部品タブの組み立て。
"""
from ipywidgets import Accordion, VBox
from .spur_gear_panel import SpurGearPanel
from .hex_bolt_panel import HexBoltPanel
from .hex_nut_panel import HexNutPanel
from .bearing_panel import BearingPanel
from .pipe_fitting_panel import PipeFittingPanel
from .v_pulley_panel import VPulleyPanel
from gui.state import AppState

def create_machine_parts_tab(state: AppState) -> VBox:
    """
    6つのパネルを組み立ててアコーディオンに入れたタブを返す
    """
    panels = [
        SpurGearPanel(),
        HexBoltPanel(),
        HexNutPanel(),
        BearingPanel(),
        PipeFittingPanel(),
        VPulleyPanel()
    ]
    accordion = Accordion(children=[p.build_widget() for p in panels])
    for i, p in enumerate(panels):
        accordion.set_title(i, p.title)
    return VBox([accordion])
