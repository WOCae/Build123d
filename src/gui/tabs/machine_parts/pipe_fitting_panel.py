"""
gui/tabs/machine_parts/pipe_fitting_panel.py
────────────────
パイプ継手（エルボ）パネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class PipeFittingPanel(MachinePartPanel):
    title = '🔄 ⑤ パイプ継手（エルボ）'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           '円弧パス上に環状断面をスイープ。'
                           '曲がり角度・パイプ径・肉厚を自由に設定できます。</div>')
        (_el1, self.elbow_od)    = self._slider('外径 D',         42.0, 10.0, 120.0, 2.0, 'mm')
        (_el2, self.elbow_t)     = self._slider('肉厚 t',          3.5,  1.0,  15.0, 0.5, 'mm')
        (_el3, self.elbow_r)     = self._slider('曲率半径 R',      60.0, 20.0, 200.0, 5.0, 'mm')
        (_el4, self.elbow_angle) = self._slider('曲がり角度 θ',    90.0, 15.0, 180.0, 5.0, '°')
        (_el5, self.elbow_ext)   = self._slider('直管延長',         20.0,  0.0,  80.0, 5.0, 'mm')
        self._rows = [_el1, _el2, _el3, _el4, _el5]
        self._btn = w.Button(description='▶ 継手を生成', button_style='primary',
                             layout=w.Layout(width='150px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('パイプ継手')
        self._btn.disabled = False
        self._btn.description = '▶ 継手を生成'

    def _build_code(self) -> str:
        od    = self.elbow_od.value
        t     = self.elbow_t.value
        R     = self.elbow_r.value
        angle = self.elbow_angle.value
        ext   = self.elbow_ext.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

outer_d = {od}    # 外径 [mm]
wall_t  = {t}     # 肉厚 [mm]
bend_R  = {R}     # 曲率半径 [mm]
angle   = {angle} # 曲がり角度 [°]
ext_len = {ext}   # 直管延長 [mm]

ro = outer_d / 2
ri = ro - wall_t

with BuildPart() as elbow:
    # ── 曲がり部（CenterArc スイープ）──
    path = CenterArc(
        center=(bend_R, 0),
        radius=bend_R,
        start_angle=180,
        arc_size=-angle
    )
    with BuildSketch(
        Plane(origin=path.start_location.position,
              z_dir=path.start_location.z_axis)
    ) as sk_pipe:
        Circle(ro)
        Circle(ri, mode=Mode.SUBTRACT)
    sweep(path=path)

    # ── 直管（入口側）──
    if ext_len > 0:
        start_pos = path.start_location.position
        start_dir = path.start_location.z_axis
        with BuildSketch(Plane(origin=start_pos, z_dir=start_dir)) as sk_ext1:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

    # ── 直管（出口側）──
    if ext_len > 0:
        end_pos = path.end_location.position
        end_dir = path.end_location.z_axis
        with BuildSketch(Plane(origin=end_pos, z_dir=end_dir)) as sk_ext2:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

export_step(elbow.part, 'output/pipe_elbow.step')
export_stl(elbow.part,  'output/pipe_elbow.stl')
show_object = elbow
print(f'✅ パイプ継手 φ{{outer_d}}×t{{wall_t}} R={{bend_R}}mm {{angle}}°')
print(f'   → output/pipe_elbow.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
