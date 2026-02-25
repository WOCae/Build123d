"""
gui/tabs/machine_parts/hex_bolt_panel.py
────────────────
六角ボルトパネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class HexBoltPanel(MachinePartPanel):
    title = '🔩 ② 六角ボルト'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        self.diameter = self._slider('呼び径', 1.0, 30.0, 0.5, 10.0, 'mm')
        self.length = self._slider('長さ', 2.0, 200.0, 1.0, 30.0, 'mm')
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('hex_bolt'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# 六角ボルト（JIS準拠）\nd = {self.diameter.value}      # 呼び径\nL = {self.length.value}        # 首下長\n\nwith BuildPart() as bolt:\n    HexBolt(diameter=d, length=L)\n\nexport_step(bolt.part, "output/hex_bolt.step")\nexport_stl(bolt.part,  "output/hex_bolt.stl")\nprint(f"✅ HexBolt: d={d}, L={L} → output/hex_bolt.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('六角ボルト パラメータ'),
            self.diameter,
            self.length,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
