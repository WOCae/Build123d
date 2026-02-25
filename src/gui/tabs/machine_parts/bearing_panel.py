"""
gui/tabs/machine_parts/bearing_panel.py
────────────────
深溝玉軸受（ベアリング）パネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class BearingPanel(MachinePartPanel):
    title = '🎯 ④ 深溝玉軸受（ベアリング）'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           '内輪・外輪・ボール・保持器を個別に生成。'
                           'JIS 呼び番号に近いサイズで調整できます。</div>')
        (_br1, self.brg_id)    = self._slider('内径 d',         20.0,  5.0, 80.0, 1.0, 'mm')
        (_br2, self.brg_od)    = self._slider('外径 D',         47.0, 15.0,120.0, 1.0, 'mm')
        (_br3, self.brg_width) = self._slider('幅 B',           14.0,  3.0, 30.0, 0.5, 'mm')
        (_br4, self.brg_balls) = self._int_slider('ボール数',     8,    4,   20, '個')
        (_br5, self.brg_ball_d)= self._slider('ボール径',         6.5,  2.0, 20.0, 0.5, 'mm')
        self._rows = [_br1, _br2, _br3, _br4, _br5]
        self._btn = w.Button(description='▶ ベアリングを生成', button_style='primary',
                             layout=w.Layout(width='160px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('深溝玉軸受')
        self._btn.disabled = False
        self._btn.description = '▶ ベアリングを生成'

    def _build_code(self) -> str:
        di = self.brg_id.value
        do = self.brg_od.value
        bw = self.brg_width.value
        nb = self.brg_balls.value
        bd = self.brg_ball_d.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

inner_d   = {di}    # 内径 [mm]
outer_d   = {do}    # 外径 [mm]
width     = {bw}    # 幅 [mm]
n_balls   = {nb}    # ボール数
ball_d    = {bd}    # ボール径 [mm]

ri = inner_d / 2
ro = outer_d / 2
race_r   = (ri + ro) / 2    # ボール軌道半径
groove_r = ball_d / 2 * 1.06

# ── 外輪（XZ断面 → revolve）──
ow = (ro - race_r) * 0.88          # 外輪の半幅
with BuildPart() as outer_ring:
    with BuildSketch(Plane.XZ) as sk_or:
        # 外輪断面（矩形 - 溝）
        with Locations((race_r + ow/2 + ball_d*0.02, 0)):
            Rectangle(ow, width)
        with Locations((race_r, 0)):
            Circle(groove_r, mode=Mode.SUBTRACT)
    revolve(axis=Axis.Z, revolution_arc=360)

# ── 内輪（XZ断面 → revolve）──
iw = (race_r - ri) * 0.88
with BuildPart() as inner_ring:
    with BuildSketch(Plane.XZ) as sk_ir:
        with Locations((ri + iw/2 + ball_d*0.02, 0)):
            Rectangle(iw, width)
        with Locations((race_r, 0)):
            Circle(groove_r, mode=Mode.SUBTRACT)
    revolve(axis=Axis.Z, revolution_arc=360)

# ── ボール群 ──
with BuildPart() as balls:
    with PolarLocations(race_r, n_balls):
        Sphere(radius=ball_d / 2)

# ── 保持器（上下リム + ポスト）──
cage_t  = ball_d * 0.22
rim_h   = width * 0.22
with BuildPart() as cage:
    # 上リム
    with BuildSketch(Plane.XY.offset(width * 0.28)) as sk_top:
        Circle(race_r + cage_t)
        Circle(race_r - cage_t, mode=Mode.SUBTRACT)
    extrude(amount=rim_h)
    # 下リム
    with BuildSketch(Plane.XY.offset(-width * 0.28 - rim_h)) as sk_bot:
        Circle(race_r + cage_t)
        Circle(race_r - cage_t, mode=Mode.SUBTRACT)
    extrude(amount=rim_h)
    # ポケット穴
    with PolarLocations(race_r, n_balls):
        Cylinder(radius=ball_d * 0.54, height=width, mode=Mode.SUBTRACT)

for part, name in [
    (outer_ring, 'bearing_outer'),
    (inner_ring, 'bearing_inner'),
    (balls,      'bearing_balls'),
    (cage,       'bearing_cage'),
]:
    export_step(part.part, f'output/{{name}}.step')
    export_stl(part.part,  f'output/{{name}}.stl')
show_object = [v for k, v in locals().items() if k in ("outer_ring", "inner_ring", "balls", "cage", "cage_parts")]

print(f'✅ 深溝玉軸受  内径{{inner_d}}×外径{{outer_d}}×幅{{width}}mm')
print(f'   ボール {{n_balls}}個 φ{{ball_d}}mm')
print(f'   → output/bearing_*.step / .stl（外輪・内輪・ボール・保持器）')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
