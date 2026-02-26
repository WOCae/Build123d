"""
gui/tabs/machine_parts/v_pulley_panel.py
────────────────
Vプーリーパネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class VPulleyPanel(MachinePartPanel):
    title = '🔘 ⑥ Vプーリー'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           'Vベルト用の溝形状を BuildSketch + revolve で生成。'
                           '溝数・プーリー径・V角度を変更できます。</div>')
        (_pl1, self.pulley_od)      = self._slider('外径 D',         100.0, 30.0, 300.0, 5.0, 'mm')
        (_pl2, self.pulley_hub)     = self._slider('ハブ径',           25.0,  8.0,  60.0, 1.0, 'mm')
        (_pl3, self.pulley_width)   = self._slider('プーリー幅',       40.0, 10.0, 120.0, 2.0, 'mm')
        (_pl4, self.pulley_grooves) = self._int_slider('溝数',          2,    1,    6,    '本')
        (_pl5, self.pulley_v_angle) = self._slider('V角度 (片側)',     17.0,  8.0,  25.0, 1.0, '°')
        (_pl6, self.pulley_groove_d)= self._slider('溝深さ',            8.0,  3.0,  20.0, 0.5, 'mm')
        self._rows = [_pl1, _pl2, _pl3, _pl4, _pl5, _pl6]
        self._btn = w.Button(description='▶ プーリーを生成', button_style='primary',
                             layout=w.Layout(width='160px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('Vプーリー')
        self._btn.disabled = False
        self._btn.description = '▶ プーリーを生成'

    def _build_code(self) -> str:
        od = self.pulley_od.value
        hd = self.pulley_hub.value
        pw = self.pulley_width.value
        ng = self.pulley_grooves.value
        va = self.pulley_v_angle.value
        gd = self.pulley_groove_d.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

outer_d    = {od}   # 外径 [mm]
hub_d      = {hd}   # ハブ径 [mm]
pwidth     = {pw}   # プーリー幅 [mm]
n_grooves  = {ng}   # 溝数
v_half     = math.radians({va})  # V角（片側）
groove_d   = {gd}   # 溝深さ [mm]
web_t      = pwidth * 0.15        # ウェブ厚さ

ro = outer_d / 2
rh = hub_d / 2
groove_spacing = pwidth / (n_grooves + 1)

with BuildPart() as pulley:
    # ── 外輪リム（回転体）──
    with BuildSketch(Plane.XZ) as sk_rim:
        with Locations((ro - 2, 0)):
            Rectangle(4, pwidth)
    revolve(axis=Axis.Z, revolution_arc=360)

    # ── ウェブ ──
    with BuildSketch(Plane.XZ) as sk_web:
        with Locations(((ro + rh) / 2, 0)):
            Rectangle(ro - rh, web_t)
    revolve(axis=Axis.Z, revolution_arc=360)

    # ── ハブ ──
    Cylinder(radius=rh + 5, height=pwidth)
    with Locations((0, 0, 0)):
        Cylinder(radius=rh, height=pwidth, mode=Mode.SUBTRACT)

    # ── V溝（複数）──
    for i in range(n_grooves):
        z_pos = -pwidth/2 + groove_spacing * (i + 1)
        groove_top_w = groove_d * math.tan(v_half) * 2
        with BuildSketch(Plane.XZ) as sk_groove:
            # V形断面（三角形）
            pts = [
                Vector(ro,            z_pos - groove_top_w / 2),
                Vector(ro - groove_d, z_pos),
                Vector(ro,            z_pos + groove_top_w / 2),
                Vector(ro + 1,        z_pos + groove_top_w / 2),
                Vector(ro + 1,        z_pos - groove_top_w / 2),
            ]
            with BuildLine() as ln:
                Polyline(pts, close=True)
            make_face()
        revolve(axis=Axis.Z, revolution_arc=360, mode=Mode.SUBTRACT)

export_step(pulley.part, 'output/v_pulley.step')
export_stl(pulley.part,  'output/v_pulley.stl')
show_object = pulley
print(f'✅ Vプーリー φ{{outer_d}} 幅{{pwidth}}mm {{n_grooves}}溝')
print(f'   → output/v_pulley.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
