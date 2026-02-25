"""
gui/tabs/machine_parts/spur_gear_panel.py
────────────────
平歯車（スパーギア）パネル。
"""
import ipywidgets as w
from .base_panel import MachinePartPanel


class SpurGearPanel(MachinePartPanel):
    title = '⚙️ ① 平歯車（スパーギア）'

    def __init__(self) -> None:
        self.log_out    = w.Output()
        self.viewer_out = w.Output()
        self.code_out   = w.Output()
        self._tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                           'インボリュート歯形を BuildSketch + spline で近似生成。'
                           'モジュール・歯数・歯幅を調整できます。</div>')
        (_r1, self.sg_module)  = self._slider('モジュール m',    2.0,  0.5,  5.0, 0.5, 'mm')
        (_r2, self.sg_teeth)   = self._int_slider('歯数 z',       20,   8,   60, '枚')
        (_r3, self.sg_width)   = self._slider('歯幅 b',          15.0,  5.0, 50.0, 1.0, 'mm')
        (_r4, self.sg_press)   = self._slider('圧力角 α',        20.0, 14.5, 25.0, 0.5, '°')
        (_r5, self.sg_hub_d)   = self._slider('ハブ径',          10.0,  0.0, 30.0, 1.0, 'mm')
        (_r6, self.sg_key_w)   = self._slider('キー溝幅',         0.0,  0.0, 10.0, 0.5, 'mm')
        self._rows = [_r1, _r2, _r3, _r4, _r5, _r6]
        self._btn = w.Button(description='▶ 歯車を生成', button_style='primary',
                             layout=w.Layout(width='150px', margin='8px 0'))
        self._btn.on_click(self._on_click)

    def _on_click(self, b: w.Button) -> None:
        self._btn.disabled = True
        self._btn.description = '実行中...'
        self._run('平歯車')
        self._btn.disabled = False
        self._btn.description = '▶ 歯車を生成'

    def _build_code(self) -> str:
        m  = self.sg_module.value
        z  = self.sg_teeth.value
        b  = self.sg_width.value
        pa = self.sg_press.value
        hd = self.sg_hub_d.value
        kw = self.sg_key_w.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

# ── パラメータ ──
m      = {m}      # モジュール [mm]
z      = {z}      # 歯数
b      = {b}      # 歯幅 [mm]
alpha  = math.radians({pa})   # 圧力角
hub_d  = {hd}     # ハブ穴径 [mm]  0=穴なし
key_w  = {kw}     # キー溝幅 [mm]  0=なし

# ── 基本寸法 ──
r   = m * z / 2
ra  = r + m
rb  = r * math.cos(alpha)
rf  = max(r - 1.25*m, rb * 0.98)
pitch = 2 * math.pi / z
t_r   = math.sqrt(max((r  / rb)**2 - 1, 0))
t_ra  = math.sqrt(max((ra / rb)**2 - 1, 0))
half  = t_r - math.atan(t_r)   # 基準円上の歯の半角

# ── ヘルパー ──
def inv(rb_, t):
    return (rb_*(math.cos(t) + t*math.sin(t)),
            rb_*(math.sin(t) - t*math.cos(t)))

def rot2d(pts, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(x*ca - y*sa, x*sa + y*ca) for x, y in pts]

# ── 1歯の点列（CCW、角度減少方向） ──
N = 10
right_flank = [inv(rb, t_ra*i/N) for i in range(N+1)]
fr = rot2d(right_flank, -half)           # 右フランク
fl = rot2d([(-x, y) for x, y in right_flank], half)  # 左フランク
fl_rev = fl[::-1]                         # 下→上方向

a_root_left  = math.atan2(fl_rev[0][1], fl_rev[0][0])
a_root_right = math.atan2(fr[0][1],     fr[0][0])

def one_tooth():
    pts = [(rf*math.cos(a_root_left), rf*math.sin(a_root_left))]
    pts.extend(fl_rev)
    a0 = math.atan2(fl_rev[-1][1], fl_rev[-1][0])
    a1 = math.atan2(fr[-1][1],     fr[-1][0])
    if a1 > a0:
        a1 -= 2*math.pi
    for k in range(1, 3):
        a = a0 + (a1 - a0)*k/3
        pts.append((ra*math.cos(a), ra*math.sin(a)))
    pts.extend(fr[::-1])
    pts.append((rf*math.cos(a_root_right), rf*math.sin(a_root_right)))
    return pts

tooth = one_tooth()

def root_arc_pt(ae, an_raw):
    an = an_raw
    while an > ae:
        an -= 2*math.pi
    return (rf*math.cos((ae + an)/2), rf*math.sin((ae + an)/2))

# ── 全歯組み立て ──
all_pts = []
for i in range(z):
    rotated = rot2d(tooth, -pitch*i)
    all_pts.extend(rotated)
    if i < z - 1:
        ae     = math.atan2(rotated[-1][1], rotated[-1][0])
        n_next = rot2d(tooth, -pitch*(i+1))
        an_raw = math.atan2(n_next[0][1], n_next[0][0])
        all_pts.append(root_arc_pt(ae, an_raw))

# ── ビルド ──
with BuildPart() as gear:
    with BuildSketch(Plane.XY) as sk:
        Polygon([Vector(x, y) for x, y in all_pts])
    extrude(amount=b)

    if hub_d > 0:
        with Locations((0, 0, b/2)):
            Cylinder(radius=hub_d/2, height=b+0.01, mode=Mode.SUBTRACT)

    if hub_d > 0 and key_w > 0:
        kd = key_w * 0.6
        with BuildSketch(Plane.XY.offset(b+0.01)) as sk_key:
            with Locations((hub_d/2 - kd/2, 0)):
                Rectangle(kd, key_w)
        extrude(amount=-(b+0.02), mode=Mode.SUBTRACT)

export_step(gear.part, 'output/spur_gear.step')
export_stl(gear.part,  'output/spur_gear.stl')
show_object = gear
print(f'✅ 平歯車 m={{m}} z={{z}} b={{b}}mm')
print(f'   基準円径: {{m*z:.2f}}mm  歯先円径: {{ra*2:.2f}}mm')
print(f'   → output/spur_gear.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
