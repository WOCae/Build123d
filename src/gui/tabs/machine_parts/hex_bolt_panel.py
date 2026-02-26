"""
gui/tabs/machine_parts/hex_bolt_panel.py
────────────────
六角ボルトパネル。
ねじ山輪郭の点列は重複点なしの台形波でPython側計算後に埋め込む。
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
                           'ねじ山は revolve で立体的に生成します。</div>')
        (_b1, self.bolt_d)        = self._slider('軸径 d',          8.0,  3.0, 24.0, 1.0,  'mm')
        (_b2, self.bolt_len)      = self._slider('首下長 L',        40.0,  5.0,150.0, 5.0,  'mm')
        (_b3, self.bolt_pitch)    = self._slider('ピッチ p',         1.25, 0.5,  4.0, 0.25, 'mm')
        (_b4, self.bolt_head_h)   = self._slider('頭部高さ',          5.0,  2.0, 20.0, 0.5,  'mm')
        (_b5, self.bolt_key_s)    = self._slider('二面幅 (対辺)',    13.0,  6.0, 46.0, 1.0,  'mm')
        (_b6, self.bolt_thread_d) = self._slider('ねじ深さ (対D比)',  0.6,  0.3,  0.9, 0.05, '×d')
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
        import math as _m

        d  = self.bolt_d.value
        L  = self.bolt_len.value
        p  = self.bolt_pitch.value
        hh = self.bolt_head_h.value
        ks = self.bolt_key_s.value
        td = self.bolt_thread_d.value

        # ── ねじ山断面の点列（重複なし台形波）──
        r       = d / 2
        thread  = r * td * 0.12
        n_turns = max(2, int(L / p))

        pts = []
        for i in range(n_turns):
            z_val = -L/2 + p * i
            z_pk  = z_val + p * 0.5
            pts.append((r,          z_val))
            pts.append((r + thread, z_pk))
        z_end = min(-L/2 + p * n_turns, L/2)
        pts.append((r, z_end))
        if abs(z_end - L/2) > 1e-6:
            pts.append((r, L/2))
        pts.append((r - thread * 0.05, L/2))
        pts.append((r - thread * 0.05, -L/2))

        pts_str = repr(pts)
        hex_r   = round(ks / _m.sqrt(3), 6)
        cham_l  = round(min(1.0, hh * 0.12), 6)

        return f"""from build123d import *
import os
os.makedirs('output', exist_ok=True)

d      = {d}
L      = {L}
pitch  = {p}
head_h = {hh}
key_s  = {ks}
hex_r  = {hex_r}
cham_l = {cham_l}

# ねじ山輪郭（計算済み・重複なし）
profile_pts = {pts_str}

with BuildPart() as bolt:
    # 軸部 + ねじ山（BuildLine -> make_face -> revolve）
    with BuildLine(Plane.XZ) as ln:
        Polyline([Vector(x, z) for x, z in profile_pts], close=True)
    with BuildSketch(Plane.XZ) as sk_shaft:
        make_face(ln.line)
    revolve(axis=Axis.Z, revolution_arc=360)

    # 頭部（六角柱）
    with BuildSketch(Plane.XY.offset(L/2)) as sk_hex:
        RegularPolygon(radius=hex_r, side_count=6)
    extrude(amount=head_h)

    # 頭部面取り
    chamfer(
        bolt.edges().filter_by_position(Axis.Z, L/2 + head_h - 0.01, L/2 + head_h + 0.01),
        length=cham_l
    )

export_step(bolt.part, 'output/hex_bolt.step')
export_stl(bolt.part,  'output/hex_bolt.stl')
show_object = bolt
print('✅ 六角ボルト M{d:.0f}x{L:.0f}  p={p}mm')
print('   頭部高: {hh}mm  二面幅: {ks}mm')
print('   -> output/hex_bolt.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
