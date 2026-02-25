"""
gui/tabs/machine_parts/bearing_panel.py
────────────────
深溝玉軸受（ベアリング）パネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class BearingPanel(MachinePartPanel):
    title = '🎯 ④ 深溝玉軸受（ベアリング）'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        self.inner = self._slider('内径', 1.0, 50.0, 0.1, 10.0, 'mm')
        self.outer = self._slider('外径', 2.0, 100.0, 0.1, 30.0, 'mm')
        self.width = self._slider('幅', 0.5, 30.0, 0.1, 5.0, 'mm')
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('bearing'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# 深溝玉軸受（ベアリング）\ninner_d = {self.inner.value}   # 内径\nouter_d = {self.outer.value}   # 外径\nwidth   = {self.width.value}   # 幅\n\nwith BuildPart() as bearing:\n    Bearing(inner_diameter=inner_d, outer_diameter=outer_d, width=width)\n\nexport_step(bearing.part, "output/bearing.step")\nexport_stl(bearing.part,  "output/bearing.stl")\nprint(f"✅ Bearing: φ{inner_d}/{outer_d}, w={width} → output/bearing.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('ベアリング パラメータ'),
            self.inner,
            self.outer,
            self.width,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
