"""
gui/tabs/machine_parts/hex_nut_panel.py
────────────────
六角ナットパネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class HexNutPanel(MachinePartPanel):
    title = '🔧 ③ 六角ナット'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           '呼び径・ナット高さ・二面幅を調整。'
                           '内部ねじ山も螺旋スイープで立体生成します。</div>')
        (_n1, self.nut_d)     = self._slider('呼び径 d',        8.0,  3.0, 24.0, 1.0,  'mm')
        (_n2, self.nut_h)     = self._slider('ナット高さ H',     6.5,  2.0, 20.0, 0.5,  'mm')
        (_n3, self.nut_key)   = self._slider('二面幅 (対辺)',   13.0,  6.0, 46.0, 1.0,  'mm')
        (_n4, self.nut_pitch) = self._slider('ピッチ p',         1.25, 0.5,  4.0, 0.25, 'mm')
        self._rows = [_n1, _n2, _n3, _n4]
        self._btn = w.Button(description='▶ ナットを生成', button_style='primary',
                             layout=w.Layout(width='150px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('六角ナット')
        self._btn.disabled = False
        self._btn.description = '▶ ナットを生成'

    def _build_code(self) -> str:
        d  = self.nut_d.value
        H  = self.nut_h.value
        ks = self.nut_key.value
        p  = self.nut_pitch.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

d      = {d}    # 呼び径 [mm]
H      = {H}    # ナット高さ [mm]
key_s  = {ks}   # 二面幅 [mm]
pitch  = {p}    # ピッチ [mm]

r  = d / 2
td = r * 0.08   # ねじ山高さ
# ── 内ねじ山断面（revolve で近似）──
n_turns = max(2, int(H / pitch))
profile_pts = [(r, -H/2)]
for i in range(n_turns):
    z0 = -H/2 + pitch * i
    z1 = z0 + pitch * 0.45
    z2 = z0 + pitch
    profile_pts += [(r - td, z0), (r, z1), (r - td, z2)]
profile_pts += [(r, H/2), (r + td*0.1, H/2), (r + td*0.1, -H/2)]

with BuildPart() as nut:
    # ── 六角柱外形 ──
    with BuildSketch(Plane.XY) as sk_hex:
        RegularPolygon(radius=key_s / math.sqrt(3), side_count=6)
    extrude(amount=H)

    # ── 内ねじ山（revolve Subtract）──
    with BuildSketch(Plane.XZ) as sk_thread:
        Polygon([Vector(x, z) for x, z in profile_pts], align=None)
    revolve(axis=Axis.Z, revolution_arc=360, mode=Mode.SUBTRACT)

    # ── 面取り（両端）──
    cl = min(1.2, H * 0.1)
    chamfer(nut.edges().filter_by_position(Axis.Z, H - 0.01, H + 0.01), length=cl)
    chamfer(nut.edges().filter_by_position(Axis.Z, -0.01, 0.01), length=cl)

export_step(nut.part, 'output/hex_nut.step')
export_stl(nut.part,  'output/hex_nut.stl')
print(f'✅ 六角ナット M{{d:.0f}}  H={{H}}mm  二面幅={{key_s}}mm')
print(f'   → output/hex_nut.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
