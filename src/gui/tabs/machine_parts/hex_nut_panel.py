"""
gui/tabs/machine_parts/hex_nut_panel.py
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
                           '内部ねじ山も revolve で立体生成します。</div>')
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
        import math as _m

        d  = self.nut_d.value
        H  = self.nut_h.value
        ks = self.nut_key.value
        p  = self.nut_pitch.value

        r       = d / 2
        td      = r * 0.08          # ねじ山高さ
        n_turns = max(2, int(H / p))
        hex_r   = round(ks / _m.sqrt(3), 6)

        # ── ねじ山断面の点列（XZ平面、Z軸まわりにrevolve）
        # X: 半径方向、Z: 軸方向
        # 内側（穴側）= 小さいX, 外側 = 大きいX
        # 断面は閉じた輪郭: 内ねじ山の「飛び出し」部分
        pts = []
        for i in range(n_turns):
            z_val = -H/2 + p * i
            z_pk  = z_val + p * 0.5
            pts.append((r - td, z_val))
            pts.append((r,      z_pk))
        z_end = min(-H/2 + p * n_turns, H/2)
        pts.append((r - td, z_end))
        if abs(z_end - H/2) > 1e-6:
            pts.append((r - td, H/2))
        # 閉じ側（外側）
        pts.append((r + td * 0.05, H/2))
        pts.append((r + td * 0.05, -H/2))

        pts_str = repr(pts)

        return f"""from build123d import *
import os
os.makedirs('output', exist_ok=True)

d     = {d}
H     = {H}
key_s = {ks}
pitch = {p}
hex_r = {hex_r}
r     = {r}
td    = {round(td, 6)}

profile_pts = {pts_str}

with BuildPart() as nut:
    # ── 六角柱外形 ──
    with BuildSketch(Plane.XY.offset(H/2)) as sk_hex:
        RegularPolygon(radius=hex_r, side_count=6)
    extrude(amount=-H)

    # ── 貫通穴（まずシンプルに円柱で穴あけ）──
    Cylinder(radius=r - td, height=H, mode=Mode.SUBTRACT)

    # ── 内ねじ山（revolve SUBTRACT）──
    with BuildLine(Plane.XZ) as ln:
        Polyline([Vector(x, z) for x, z in profile_pts], close=True)
    with BuildSketch(Plane.XZ) as sk_thread:
        make_face(ln.line)
    revolve(axis=Axis.Z, revolution_arc=360, mode=Mode.SUBTRACT)

export_step(nut.part, 'output/hex_nut.step')
export_stl(nut.part,  'output/hex_nut.stl')
show_object = nut
print('✅ 六角ナット M{d:.0f}  H={H}mm  二面幅={ks}mm')
print('   -> output/hex_nut.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
