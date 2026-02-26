"""
gui/tabs/machine_parts/pipe_fitting_panel.py
────────────────
パイプ継手（エルボ）パネル。
【修正】CenterArc は BuildLine 内で使用し、sweep のパスとして渡す正しい方法に変更。
直管延長は elbow 端面から押し出す方式に変更。
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
        (_el1, self.elbow_od)    = self._slider('外径 D',       42.0, 10.0, 120.0, 2.0, 'mm')
        (_el2, self.elbow_t)     = self._slider('肉厚 t',        3.5,  1.0,  15.0, 0.5, 'mm')
        (_el3, self.elbow_r)     = self._slider('曲率半径 R',    60.0, 20.0, 200.0, 5.0, 'mm')
        (_el4, self.elbow_angle) = self._slider('曲がり角度 θ',  90.0, 15.0, 180.0, 5.0, '°')
        (_el5, self.elbow_ext)   = self._slider('直管延長',       20.0,  0.0,  80.0, 5.0, 'mm')
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

        return f"""from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

outer_d = {od}
wall_t  = {t}
bend_R  = {R}
angle   = {angle}
ext_len = {ext}

ro = outer_d / 2
ri = ro - wall_t

with BuildPart() as elbow:
    # ── 曲がり部: BuildLine で円弧パスを作り sweep ──
    with BuildLine(Plane.XZ) as path_line:
        CenterArc(
            center=(bend_R, 0),
            radius=bend_R,
            start_angle=180,
            arc_size=-angle
        )

    # スイープ断面: パス始端の平面上にリング
    path_wire = path_line.wires()[0]
    start_pt  = path_wire.start_point()          # Vector
    start_tan = path_wire.tangent_at(0)          # 始端接線方向
    sweep_plane = Plane(origin=start_pt, z_dir=start_tan)

    with BuildSketch(sweep_plane) as sk_pipe:
        Circle(ro)
        Circle(ri, mode=Mode.SUBTRACT)
    sweep(path=path_wire)

    # ── 直管延長: 両端面から押し出し ──
    if ext_len > 0:
        # 入口側: start_pt 方向に -start_tan で押し出し
        with BuildSketch(Plane(origin=start_pt, z_dir=-start_tan)) as sk_in:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

        # 出口側: パス終端
        end_pt  = path_wire.end_point()
        end_tan = path_wire.tangent_at(1)
        with BuildSketch(Plane(origin=end_pt, z_dir=end_tan)) as sk_out:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

export_step(elbow.part, 'output/pipe_elbow.step')
export_stl(elbow.part,  'output/pipe_elbow.stl')
show_object = elbow
print(f'✅ パイプ継手 phi{od}xt{t} R={R}mm {angle}deg')
print(f'   -> output/pipe_elbow.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])