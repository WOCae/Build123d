"""
gui/tabs/machine_parts/v_pulley_panel.py
────────────────
Vプーリーパネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class VPulleyPanel(MachinePartPanel):
    title = '🔘 ⑥ Vプーリー'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        self.diameter = self._slider('プーリー径', 10.0, 500.0, 1.0, 100.0, 'mm')
        self.width = self._slider('幅', 5.0, 100.0, 0.5, 20.0, 'mm')
        self.groove = self._slider('溝数', 1, 10, 1, 1)
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('v_pulley'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# Vプーリー\nd = {self.diameter.value}      # プーリー径\nw = {self.width.value}         # 幅\ngrooves = {self.groove.value}  # 溝数\n\nwith BuildPart() as pulley:\n    VPulley(diameter=d, width=w, grooves=grooves)\n\nexport_step(pulley.part, "output/v_pulley.step")\nexport_stl(pulley.part,  "output/v_pulley.stl")\nprint(f"✅ VPulley: d={d}, w={w}, grooves={grooves} → output/v_pulley.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('Vプーリー パラメータ'),
            self.diameter,
            self.width,
            self.groove,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
