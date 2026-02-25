"""
gui/tabs/machine_parts/hex_bolt_panel.py
────────────────
六角ボルトパネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class HexBoltPanel(MachinePartPanel):
    title = '🔩 ② 六角ボルト'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           '軸径・首下長・ねじピッチ・頭部サイズを調整。'
                           'ねじ山は螺旋スイープで立体的に生成します。</div>')
        (_b1, self.bolt_d)       = self._slider('軸径 d',          8.0,  3.0, 24.0, 1.0,  'mm')
        (_b2, self.bolt_len)     = self._slider('首下長 L',        40.0,  5.0,150.0, 5.0,  'mm')
        (_b3, self.bolt_pitch)   = self._slider('ピッチ p',         1.25, 0.5,  4.0, 0.25, 'mm')
        (_b4, self.bolt_head_h)  = self._slider('頭部高さ',          5.0,  2.0, 20.0, 0.5,  'mm')
        (_b5, self.bolt_key_s)   = self._slider('二面幅 (対辺)',    13.0,  6.0, 46.0, 1.0,  'mm')
        (_b6, self.bolt_thread_d)= self._slider('ねじ深さ (対D比)',  0.6,  0.3,  0.9, 0.05, '×d')
        self._rows = [_b1, _b2, _b3, _b4, _b5, _b6]
        self._btn = w.Button(description='▶ ボルトを生成', button_style='primary',
                             layout=w.Layout(width='150px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('六角ボルト')
        self._btn.disabled = False
        self._btn.description = '▶ ボルトを生成'

    def _build_code(self) -> str:
        d  = self.bolt_d.value
        L  = self.bolt_len.value
        p  = self.bolt_pitch.value
        hh = self.bolt_head_h.value
        ks = self.bolt_key_s.value
        td = self.bolt_thread_d.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

# ── パラメータ ──
d        = {d}     # 軸径 [mm]
L        = {L}     # 首下長 [mm]
pitch    = {p}     # ねじピッチ [mm]
head_h   = {hh}    # 頭部高さ [mm]
key_s    = {ks}    # 二面幅（対辺） [mm]
td_ratio = {td}    # ねじ山深さ比率

r  = d / 2
td = r * td_ratio * 0.12   # ねじ山高さ
# ── ねじ山断面を回転体で近似（軽量）──
# XZ断面: ノコギリ波輪郭を revolve
n_turns = max(2, int(L / pitch))
z_pts   = []
r_pts   = []
for i in range(n_turns):
    z0 = -L/2 + pitch * i
    z1 = z0 + pitch * 0.45
    z2 = z0 + pitch
    z_pts += [z0, z1, z2]
    r_pts += [r, r + td, r]
# 輪郭を閉じる（軸側）
profile_pts = (
    [(r,  -L/2)]
    + list(zip(r_pts, z_pts))
    + [(r,   L/2), (r - td*0.1, L/2), (r - td*0.1, -L/2)]
)

with BuildPart() as bolt:
    # ── 軸部 + ねじ山（revolve）──
    with BuildSketch(Plane.XZ) as sk_shaft:
        make_face(Polyline([Vector(x, z) for x, z in profile_pts], close=True))
    revolve(axis=Axis.Z, revolution_arc=360)

    # ── 頭部（六角柱）──
    with BuildSketch(Plane.XY.offset(L/2)) as sk_hex:
        RegularPolygon(radius=key_s / math.sqrt(3), side_count=6)
    extrude(amount=head_h)

    # 頭部面取り
    chamfer(
        bolt.edges().filter_by_position(Axis.Z, L/2 + head_h - 0.01, L/2 + head_h + 0.01),
        length=min(1.0, head_h * 0.12)
    )

export_step(bolt.part, 'output/hex_bolt.step')
export_stl(bolt.part,  'output/hex_bolt.stl')
show_object = bolt
print(f'✅ 六角ボルト M{{d:.0f}}×{{L:.0f}}  p={{pitch}}mm')
print(f'   頭部高: {{head_h}}mm  二面幅: {{key_s}}mm')
print(f'   → output/hex_bolt.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
