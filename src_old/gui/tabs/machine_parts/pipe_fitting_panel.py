"""
gui/tabs/machine_parts/pipe_fitting_panel.py
────────────────
パイプ継手（エルボ）パネル。
"""
from ipywidgets import VBox, Output, Button
from .base_panel import MachinePartPanel

class PipeFittingPanel(MachinePartPanel):
    title = '🔄 ⑤ パイプ継手（エルボ）'

    def __init__(self) -> None:
        self.log_out = Output()
        self.viewer_out = Output()
        self.code_out = Output()
        self.diameter = self._slider('パイプ径', 1.0, 100.0, 0.5, 20.0, 'mm')
        self.angle = self._slider('角度', 30.0, 180.0, 1.0, 90.0, '°')
        self.radius = self._slider('曲げ半径', 5.0, 100.0, 0.5, 20.0, 'mm')
        self.button = Button(description='生成', button_style='success')
        self.button.on_click(lambda _: self._run('pipe_fitting'))

    def _build_code(self) -> str:
        # f-stringは絶対に変更しないこと
        return f'''from build123d import *\n\n# パイプ継手（エルボ）\nd = {self.diameter.value}      # パイプ径\nangle = {self.angle.value}     # 角度\nradius = {self.radius.value}   # 曲げ半径\n\nwith BuildPart() as elbow:\n    PipeElbow(diameter=d, angle=angle, bend_radius=radius)\n\nexport_step(elbow.part, "output/pipe_elbow.step")\nexport_stl(elbow.part,  "output/pipe_elbow.stl")\nprint(f"✅ PipeElbow: d={d}, angle={angle}, r={radius} → output/pipe_elbow.step / .stl")\n'''

    def build_widget(self) -> VBox:
        return VBox([
            self._section('パイプ継手 パラメータ'),
            self.diameter,
            self.angle,
            self.radius,
            self.button,
            self.code_out,
            self.viewer_out,
            self.log_out
        ])
