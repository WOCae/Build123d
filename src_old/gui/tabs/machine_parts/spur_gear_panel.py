"""
gui/tabs/machine_parts/spur_gear_panel.py
────────────────
スパーギア（平歯車）パネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class SpurGearPanel(MachinePartPanel):
    title = '⚙️ ① 平歯車（スパーギア）'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        # スライダー等のウィジェット定義
        self.module = self._slider('モジュール', 0.5, 10.0, 0.1, 2.0, 'mm')
        self.teeth = self._int_slider('歯数', 6, 100, 1, 20)
        self.width = self._slider('歯幅', 1.0, 50.0, 0.1, 10.0, 'mm')
        self.hole = self._slider('穴径', 0.0, 30.0, 0.1, 5.0, 'mm')
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('spur_gear'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# 平歯車（スパーギア）\nmodule = {self.module.value}  # モジュール\nteeth = {self.teeth.value}    # 歯数\nwidth = {self.width.value}    # 歯幅\nhole_d = {self.hole.value}    # 穴径\n\nwith BuildPart() as gear:\n    SpurGear(module=module, teeth=teeth, width=width)\n    if hole_d > 0:\n        with Locations((0, 0, 0)):\n            Cylinder(radius=hole_d/2, height=width+2, mode=Mode.SUBTRACT)\n\nexport_step(gear.part, "output/spur_gear.step")\nexport_stl(gear.part,  "output/spur_gear.stl")\nprint(f"✅ SpurGear: m={module}, z={teeth}, w={width} → output/spur_gear.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('スパーギア パラメータ'),
            self.module,
            self.teeth,
            self.width,
            self.hole,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
