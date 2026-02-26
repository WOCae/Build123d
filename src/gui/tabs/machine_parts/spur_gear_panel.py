"""
gui/tabs/machine_parts/spur_gear_panel.py
────────────────
平歯車（スパーギア）パネル。
【アプローチ】
  1. 歯底円ディスクを作成
  2. 各歯1本ずつ点列→Polyline→make_face→extrude→Addする
  この方式はmake_faceに渡すワイヤーが各歯の単純な閉曲線なので確実に動作する。
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
                           'インボリュート歯形を近似生成。'
                           'モジュール・歯数・歯幅を調整できます。</div>')
        (_r1, self.sg_module) = self._slider('モジュール m',  2.0,  0.5,  5.0, 0.5, 'mm')
        (_r2, self.sg_teeth)  = self._int_slider('歯数 z',    20,   8,   60, '枚')
        (_r3, self.sg_width)  = self._slider('歯幅 b',       15.0,  5.0, 50.0, 1.0, 'mm')
        (_r4, self.sg_press)  = self._slider('圧力角 α',     20.0, 14.5, 25.0, 0.5, '°')
        (_r5, self.sg_hub_d)  = self._slider('ハブ径',       10.0,  0.0, 30.0, 1.0, 'mm')
        (_r6, self.sg_key_w)  = self._slider('キー溝幅',      0.0,  0.0, 10.0, 0.5, 'mm')
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
        import math as _m

        m  = self.sg_module.value
        z  = self.sg_teeth.value
        b  = self.sg_width.value
        pa = self.sg_press.value
        hd = self.sg_hub_d.value
        kw = self.sg_key_w.value

        # ── インボリュート歯形計算 ──
        alpha = _m.radians(pa)
        r     = m * z / 2
        ra    = r + m
        rb    = r * _m.cos(alpha)
        rf    = max(r - 1.25*m, rb * 0.98)
        pitch = 2 * _m.pi / z
        t_r   = _m.sqrt(max((r  / rb)**2 - 1, 0))
        t_ra  = _m.sqrt(max((ra / rb)**2 - 1, 0))
        half  = t_r - _m.atan(t_r)

        def inv(rb_, t):
            return (rb_*(_m.cos(t)+t*_m.sin(t)), rb_*(_m.sin(t)-t*_m.cos(t)))

        def rot2d(pts, a):
            ca, sa = _m.cos(a), _m.sin(a)
            return [(x*ca-y*sa, x*sa+y*ca) for x, y in pts]

        N = 10
        right_flank = [inv(rb, t_ra*i/N) for i in range(N+1)]
        fr = rot2d(right_flank, -half)
        fl = rot2d([(-x, y) for x, y in right_flank], half)
        fl_rev = fl[::-1]

        a_root_left  = _m.atan2(fl_rev[0][1],  fl_rev[0][0])
        a_root_right = _m.atan2(fr[0][1],       fr[0][0])
        a_tip_l = _m.atan2(fl_rev[-1][1], fl_rev[-1][0])
        a_tip_r = _m.atan2(fr[-1][1],     fr[-1][0])
        if a_tip_r > a_tip_l:
            a_tip_r -= 2*_m.pi
        # 歯先弧（補間点）
        N_arc = 4
        tip_arc = [(ra*_m.cos(a_tip_l+(a_tip_r-a_tip_l)*k/N_arc),
                    ra*_m.sin(a_tip_l+(a_tip_r-a_tip_l)*k/N_arc))
                   for k in range(1, N_arc)]

        def one_tooth():
            pts = [(rf*_m.cos(a_root_left), rf*_m.sin(a_root_left))]
            pts.extend(fl_rev)
            pts.extend(tip_arc)
            pts.extend(fr[::-1])
            pts.append((rf*_m.cos(a_root_right), rf*_m.sin(a_root_right)))
            # 歯底円中心を経由して閉じる（扇形）
            # 中心を通る閉じた輪郭にする → (0,0) を追加
            pts.append((0.0, 0.0))
            return pts

        tooth = one_tooth()

        # 全歯の輪郭リストを生成（各歯を個別リストで保持）
        all_teeth = []
        for i in range(z):
            rotated = rot2d(tooth, -pitch * i)
            # 重複除去
            clean = [rotated[0]]
            for p in rotated[1:]:
                if _m.hypot(p[0]-clean[-1][0], p[1]-clean[-1][1]) > 1e-6:
                    clean.append(p)
            all_teeth.append(clean)

        teeth_str = repr(all_teeth)

        hub_block = ''
        if hd > 0:
            hub_block = f'\n    Cylinder(radius={hd/2}, height=b, mode=Mode.SUBTRACT)'

        key_block = ''
        if hd > 0 and kw > 0:
            kd = round(kw*0.6, 4)
            key_block = f"""
    with BuildSketch(Plane.XY) as sk_key:
        with Locations(({hd/2-kd/2:.4f}, 0)):
            Rectangle({kd}, {kw})
    extrude(amount=-b, mode=Mode.SUBTRACT)"""

        return f"""from build123d import *
import os
os.makedirs('output', exist_ok=True)

m   = {m}
z   = {z}
b   = {b}
ra  = {ra:.6f}
rf  = {rf:.6f}

all_teeth = {teeth_str}

with BuildPart() as gear:
    # ── Step1: 歯底円ディスク ──
    with BuildSketch(Plane.XY) as sk_base:
        Circle(rf)
    extrude(amount=b)

    # ── Step2: 各歯を1本ずつ追加 ──
    for tooth_pts in all_teeth:
        with BuildSketch(Plane.XY) as sk_tooth:
            with BuildLine() as ln:
                Polyline([Vector(x, y, 0) for x, y in tooth_pts], close=True)
            make_face()
        extrude(amount=b, mode=Mode.ADD)
{hub_block}{key_block}

export_step(gear.part, 'output/spur_gear.step')
export_stl(gear.part,  'output/spur_gear.stl')
show_object = gear
print('✅ 平歯車 m={m} z={z} b={b}mm')
print('   基準円径: {m*z:.2f}mm  歯先円径: {ra*2:.2f}mm')
print('   -> output/spur_gear.step / .stl')
"""

    def build_widget(self) -> w.VBox:
        return w.VBox([
            self._section(self.title),
            self._tip,
            *self._rows,
            self._btn,
        ])
