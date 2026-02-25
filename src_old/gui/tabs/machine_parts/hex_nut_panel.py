"""
gui/tabs/machine_parts/hex_nut_panel.py
────────────────
六角ナットパネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class HexNutPanel(MachinePartPanel):
    title = '🔧 ③ 六角ナット'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        self.diameter = self._slider('呼び径', 1.0, 30.0, 0.5, 10.0, 'mm')
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('hex_nut'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# 六角ナット（JIS準拠）\nd = {self.diameter.value}      # 呼び径\n\nwith BuildPart() as nut:\n    HexNut(diameter=d)\n\nexport_step(nut.part, "output/hex_nut.step")\nexport_stl(nut.part,  "output/hex_nut.stl")\nprint(f"✅ HexNut: d={d} → output/hex_nut.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('六角ナット パラメータ'),
            self.diameter,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
