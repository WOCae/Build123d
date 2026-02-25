"""
gui/tabs/samples_tab.py
────────────────
サンプルタブのUI生成。
"""
import ipywidgets as w
from IPython.display import display, HTML
from gui.utils.code_utils import run_code
from gui.utils.viewer import _find_latest_stl, _show_viewer


SAMPLES = [
    {
        'id': 'basic_shapes',
        'label': '① 基本形状（Box / Cylinder / Sphere）',
        'desc': (
            '<b>Box（直方体）</b>: 幅100 × 奥行50 × 高さ30 mm<br>'
            '<b>Cylinder（円柱）</b>: 半径25 mm、高さ80 mm<br>'
            '<b>Sphere（球）</b>: 半径20 mm<br>'
            '<span class="cad-tip">build123d の最も基本的な3形状です。それぞれ独立した .step / .stl を出力します。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

# Box
with BuildPart() as box_part:
    Box(100, 50, 30)
export_step(box_part.part, 'output/sample_box.step')
export_stl(box_part.part,  'output/sample_box.stl')
print(f'✅ Box: 体積={box_part.part.volume:.1f} mm³  → output/sample_box.step / .stl')

# Cylinder
with BuildPart() as cyl_part:
    Cylinder(radius=25, height=80)
export_step(cyl_part.part, 'output/sample_cylinder.step')
export_stl(cyl_part.part,  'output/sample_cylinder.stl')
print(f'✅ Cylinder: 体積={cyl_part.part.volume:.1f} mm³  → output/sample_cylinder.step / .stl')

# Sphere
with BuildPart() as sph_part:
    Sphere(radius=20)
export_step(sph_part.part, 'output/sample_sphere.step')
export_stl(sph_part.part,  'output/sample_sphere.stl')
print(f'✅ Sphere: 体積={sph_part.part.volume:.1f} mm³  → output/sample_sphere.step / .stl')
""",
    },
    {
        'id': 'boolean_union',
        'label': '② ブーリアン合体（Union）',
        'desc': (
            'Box（60×60×20 mm）の上に Cylinder（半径15 mm、高さ40 mm）を合体させた形状。<br>'
            '<b>mode=Mode.ADD</b>（デフォルト）で自動的に合体されます。<br>'
            '<span class="cad-tip">複数の形状を同じ BuildPart コンテキスト内に置くだけで Union になります。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as union_part:
    Box(60, 60, 20)
    Cylinder(radius=15, height=40)

export_step(union_part.part, 'output/sample_union.step')
export_stl(union_part.part,  'output/sample_union.stl')
print(f'✅ Union 合体: 体積={union_part.part.volume:.1f} mm³  → output/sample_union.step / .stl')
""",
    },
    {
        'id': 'boolean_subtract',
        'label': '③ ブーリアン引き算（Subtract / 穴あき）',
        'desc': (
            'Box（80×80×30 mm）の中央に Cylinder（半径20 mm）で貫通穴を開けた形状。<br>'
            '<b>mode=Mode.SUBTRACT</b> を指定することで引き算になります。<br>'
            '<span class="cad-tip">穴・溝・切り欠きはすべてこのパターンで作れます。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as hole_part:
    Box(80, 80, 30)
    with Locations((0, 0, 0)):
        Cylinder(radius=20, height=30, mode=Mode.SUBTRACT)

export_step(hole_part.part, 'output/sample_subtract.step')
export_stl(hole_part.part,  'output/sample_subtract.stl')
print(f'✅ Subtract 穴あき: 体積={hole_part.part.volume:.1f} mm³  → output/sample_subtract.step / .stl')
""",
    },
    {
        'id': 'bolt_plate',
        'label': '④ ボルト穴パターン（GridLocations）',
        'desc': (
            'Box（100×100×15 mm）の四隅にボルト穴（φ10 mm、70 mmピッチ）を配置。<br>'
            '<b>GridLocations</b> で均等グリッドに穴を自動配置します。<br>'
            '<span class="cad-tip">PolarLocations（円周均等配置）と組み合わせると機械部品に応用できます。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as bolt_plate:
    Box(100, 100, 15)
    with GridLocations(70, 70, 2, 2):
        Cylinder(radius=5, height=15, mode=Mode.SUBTRACT)

export_step(bolt_plate.part, 'output/sample_bolt_plate.step')
export_stl(bolt_plate.part,  'output/sample_bolt_plate.stl')
print(f'✅ ボルト穴プレート: 体積={bolt_plate.part.volume:.1f} mm³  → output/sample_bolt_plate.step / .stl')
""",
    },
    {
        'id': 'fillet_chamfer',
        'label': '⑤ フィレット・面取り（fillet / chamfer）',
        'desc': (
            '<b>フィレット（R5）</b>: Box（80×60×25 mm）のすべてのエッジを丸める。<br>'
            '<b>面取り（C3）</b>: 同形状のエッジをC3で面取り。<br>'
            '<span class="cad-tip">fillet / chamfer はグローバル関数として、形状確定後に呼びます。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

with BuildPart() as fillet_part:
    Box(80, 60, 25)
    fillet(fillet_part.edges(), radius=5)
export_step(fillet_part.part, 'output/sample_fillet.step')
export_stl(fillet_part.part,  'output/sample_fillet.stl')
print(f'✅ フィレット R5: 体積={fillet_part.part.volume:.1f} mm³  → output/sample_fillet.step / .stl')

with BuildPart() as chamfer_part:
    Box(80, 60, 25)
    chamfer(chamfer_part.edges(), length=3)
export_step(chamfer_part.part, 'output/sample_chamfer.step')
export_stl(chamfer_part.part,  'output/sample_chamfer.stl')
print(f'✅ 面取り C3: 体積={chamfer_part.part.volume:.1f} mm³  → output/sample_chamfer.step / .stl')
""",
    },
    {
        'id': 'flange_shaft',
        'label': '⑥ 機械部品：フランジ付きシャフト',
        'desc': (
            'シャフト径 φ30 mm、長さ 120 mm に<br>'
            'フランジ（φ80 mm、厚さ 15 mm）を合体し、ボルト穴 4×φ10 mm（PCD φ60 mm）付き。<br>'
            'シャフト根元に R3 フィレット。<br>'
            '<span class="cad-tip">LLM が生成するコードの典型的な例です。パラメータを変えて応用できます。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

shaft_diameter   = 30
shaft_length     = 120
flange_diameter  = 80
flange_thickness = 15
bolt_hole_dia    = 10
bolt_pcd         = 60
n_bolts          = 4
fillet_r         = 3

with BuildPart() as flange_shaft:
    Cylinder(radius=shaft_diameter/2, height=shaft_length)
    with Locations((0, 0, -shaft_length/2 + flange_thickness/2)):
        Cylinder(radius=flange_diameter/2, height=flange_thickness)
    with PolarLocations(bolt_pcd/2, n_bolts):
        Cylinder(radius=bolt_hole_dia/2, height=flange_thickness, mode=Mode.SUBTRACT)
    fillet(
        flange_shaft.edges().filter_by_position(
            Axis.Z,
            -shaft_length/2 + flange_thickness,
            -shaft_length/2 + flange_thickness + 1
        ),
        radius=fillet_r
    )

export_step(flange_shaft.part, 'output/sample_flange_shaft.step')
export_stl(flange_shaft.part,  'output/sample_flange_shaft.stl')
print(f'✅ フランジ付きシャフト: 体積={flange_shaft.part.volume:.1f} mm³')
print(f'   シャフト径: {shaft_diameter}mm, 長さ: {shaft_length}mm')
print(f'   フランジ径: {flange_diameter}mm, ボルト穴: {n_bolts}×φ{bolt_hole_dia}mm')
print(f'   → output/sample_flange_shaft.step / .stl')
""",
    },
    {
        'id': 'l_bracket',
        'label': '⑦ 機械部品：Lブラケット',
        'desc': (
            '幅60 mm、高さ80 mm、奥行き50 mm、板厚8 mm の L 字ブラケット。<br>'
            '縦板と横板を Union で合体し、接合エッジに R5 フィレット。<br>'
            '<span class="cad-tip">Locations で配置した Box を Union することで L 字・T 字形状を作れます。</span>'
        ),
        'code': """\
from build123d import *
import os
os.makedirs('output', exist_ok=True)

width     = 60
height    = 80
depth     = 50
thickness = 8

with BuildPart() as l_bracket:
    Box(thickness, width, height)
    with Locations((depth/2, 0, -height/2 + thickness/2)):
        Box(depth, width, thickness)
    fillet(l_bracket.edges().filter_by_position(Axis.X, 0, 1), radius=5)

export_step(l_bracket.part, 'output/sample_l_bracket.step')
export_stl(l_bracket.part,  'output/sample_l_bracket.stl')
print(f'✅ Lブラケット: 体積={l_bracket.part.volume:.1f} mm³')
print(f'   幅:{width}mm 高さ:{height}mm 奥行き:{depth}mm 板厚:{thickness}mm')
print(f'   → output/sample_l_bracket.step / .stl')
""",
    },
]


def create_samples_tab() -> w.VBox:
    """サンプルタブのUIを返す。"""
    sample_log_out    = w.Output()
    sample_code_out   = w.Output()
    sample_viewer_out = w.Output()

    def _run_sample(code: str, label: str) -> None:
        sample_log_out.clear_output()
        sample_code_out.clear_output()
        sample_viewer_out.clear_output()
        with sample_code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))
        with sample_log_out:
            print(f'▶ {label} を実行中...')
        ok, err = run_code(code)
        if ok:
            with sample_log_out:
                print('✅ 生成完了！  output/ フォルダを確認してください。')
            stl = _find_latest_stl(code)
            if stl:
                _show_viewer(stl, sample_viewer_out)
        else:
            with sample_log_out:
                print(f'❌ エラー:\n{err}')

    def _make_sample_row(s: dict) -> w.HBox:
        btn = w.Button(description='▶ 生成', button_style='success',
                       layout=w.Layout(width='90px', height='36px'))
        desc_html = w.HTML(
            f'<div style="font-size:13px;font-weight:600;margin-bottom:3px">{s["label"]}</div>'
            f'<div style="font-size:12px;line-height:1.6">{s["desc"]}</div>'
        )
        row = w.HBox([btn, desc_html], layout=w.Layout(
            padding='10px', margin='4px 0', border='1px solid #dee2e6',
            border_radius='6px', align_items='flex-start', gap='14px'))

        def on_click(b, _code=s['code'], _label=s['label']):
            btn.disabled = True; btn.description = '実行中...'
            _run_sample(_code, _label)
            btn.disabled = False; btn.description = '▶ 生成'

        btn.on_click(on_click)
        return row

    sample_rows = [_make_sample_row(s) for s in SAMPLES]

    return w.VBox([
        w.HTML('<div style="font-size:13px;color:#555;margin-bottom:8px">'
               '▶ 生成 ボタンを押すとコードが表示され、STEP/STL が <code>output/</code> に保存されます。</div>'),
        *sample_rows,
        w.HTML('<hr style="margin:10px 0"><b>実行ログ</b>'),
        sample_log_out,
        w.HTML('<b>🖥️ 3Dビューア</b>'),
        sample_viewer_out,
        w.HTML('<b>実行コード</b>'),
        sample_code_out,
    ], layout=w.Layout(padding='10px'))
