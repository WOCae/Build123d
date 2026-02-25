"""
build123d_gui.py
────────────────
Build123d × LLM ダッシュボード
インポートして display_dashboard() を呼ぶだけで完全なGUIが表示されます。

使い方:
    import build123d_gui
    build123d_gui.display_dashboard()
"""

import sys, os, ast, re, textwrap, traceback, subprocess, importlib

import ipywidgets as w
from IPython.display import display, HTML, clear_output


os.makedirs('output', exist_ok=True)


# ══════════════════════════════════════════════════════════════
# 依存ライブラリの自動インストール
# ══════════════════════════════════════════════════════════════
def _ensure_deps():
    pkgs = {
        'ipywidgets': 'ipywidgets',
        'anthropic':  'anthropic',
        'openai':     'openai',
        'google.genai': 'google-genai',
    }
    needs_restart = False
    for mod, pkg in pkgs.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', pkg], check=True)
            needs_restart = True

    if needs_restart:
        try:
            from google.colab import runtime
            print('🔄 ライブラリをインストールしました。ランタイムを再起動します...')
            print('   再起動後、このセルをもう一度実行してください。')
            runtime.unassign()
        except ImportError:
            print('✅ ライブラリインストール完了（ローカル環境）')

# ══════════════════════════════════════════════════════════════
# 状態管理
# ══════════════════════════════════════════════════════════════
state = dict(
    llm_mode        = 'manual',
    provider        = 'google',
    anthropic_key   = '',
    openai_key      = '',
    google_key      = '',
    anthropic_model = 'claude-opus-4-6',
    openai_model    = 'gpt-4o',
    google_model    = 'gemini-2.5-flash',
    history         = [],
    last_code       = '',
    last_err        = '',
    last_raw        = '',
)

# ══════════════════════════════════════════════════════════════
# システムプロンプト
# ══════════════════════════════════════════════════════════════
SYSTEM_PROMPT = textwrap.dedent("""\
    あなたはBuild123dのエキスパートです。以下のルールに従ってPythonコードを生成してください。

    【ルール】
    1. 必ず `from build123d import *` でインポートする
    2. 形状は `with BuildPart() as part:` のコンテキストマネージャ内に書く
    3. 寸法はすべてmm単位のfloatまたはintで書く
    4. パラメータは変数として冒頭にまとめて定義する
    5. ブーリアン演算は mode=Mode.SUBTRACT（穴）または mode=Mode.ADD（合体）を使う
    6. BuildSketch はネストせず、mode=Mode.SUBTRACT で内穴を作る
    7. fillet はすべての形状確定後、最後に適用する
    8. 最後に必ずこの2行を含める:
       export_step(part.part, "output/llm_output.step")
       export_stl(part.part, "output/llm_output.stl")
    9. 【最重要】必ずコードブロック(```python\\n...\\n```)のみ返す。
       日本語の説明・コメントをコードブロックの外に書かない。
       返答の最初の文字は ``` でなければならない。

    【基本形状】Box / Cylinder / Sphere / Cone
    【配置】Locations / PolarLocations / GridLocations

    【fillet / chamfer の正しい書き方 ─ 最重要】
    # ✅ 正しい: グローバル関数として呼び出す
    with BuildPart() as part:
        Box(100, 100, 30)
        fillet(part.edges(), radius=5)        # part.edges() を渡す
        chamfer(part.edges(), length=3)       # chamfer も同様

    # ❌ 誤り（AttributeError になる）
    # part.fillet(...)   ← BuildPart オブジェクトにはfilletメソッドはない
    # part.part.fillet(...) ← これも不可

    【よくある間違い】
    - BuildSketchのネスト禁止
    - fillet/chamfer は必ず形状確定後にグローバル関数で呼ぶ
    - part.edges() の代わりに part.part.edges() と書かない
    - filter_by_orientation / filter_by_axis は存在しない → 使わない
    - 特定エッジだけにfilletしたい場合は filter_by_position(Axis.Z, min, max) を使う
      例: fillet(part.edges().filter_by_position(Axis.Z, 0, height), radius=3)
""")

BANNED = ['os.system','subprocess','eval(','exec(','__import__','shutil.','requests.','urllib']

# ══════════════════════════════════════════════════════════════
# コード処理ユーティリティ
# ══════════════════════════════════════════════════════════════
def extract_code(text):
    """LLMの返答からPythonコードブロックを確実に抽出する"""
    m = re.search(r'```(?:python)?[ \t]*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'(from build123d import.*)', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ''

def validate_code_block(code, raw_response):
    if not code:
        return False, (
            'LLMがコードブロックを返しませんでした。\n'
            f'LLMの返答（先頭200文字）:\n{raw_response[:200]}'
        )
    if 'from build123d' not in code and 'BuildPart' not in code:
        return False, (
            'Build123dのコードが含まれていません。\n'
            f'抽出されたテキスト（先頭200文字）:\n{code[:200]}'
        patches.append(f'  {varname}.fillet({args}) → fillet({varname}.edges(), {args})')
        """
        build123d_gui.py
        ────────────────
        Build123d × LLM ダッシュボード
        インポートして display_dashboard() を呼ぶだけで完全なGUIが表示されます。

        使い方:
            import build123d_gui
            build123d_gui.display_dashboard()
        """

        from gui.dashboard import display_dashboard

        __all__ = ['display_dashboard']
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

    # ── STL インラインビューア ────────────────────────────────
    def _make_viewer_html(stl_path):
        """STLファイルをBase64エンコードしてThree.jsビューアのHTMLを返す"""
        import base64
        with open(stl_path, 'rb') as f:
            stl_b64 = base64.b64encode(f.read()).decode()
        fname = os.path.basename(stl_path)
        # ユニークID（同一ノートブック内で複数ビューア共存できるよう）
        uid = f'v{abs(hash(stl_path)) % 99999:05d}'
        return f"""
<div id="wrap_{uid}" style="position:relative;width:100%;max-width:700px;margin:8px 0">
  <div style="font-size:12px;color:#555;margin-bottom:4px">
    🖱️ ドラッグ: 回転 ／ ホイール: ズーム ／ 右ドラッグ: 平行移動
    <span style="float:right;color:#888">{fname}</span>
  </div>
  <canvas id="c_{uid}" style="width:100%;height:420px;border-radius:8px;
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    display:block"></canvas>
  <div id="err_{uid}" style="color:#f66;font-size:12px;display:none;padding:8px"></div>
</div>
<script>
(function(){{
  var STL_B64 = "{stl_b64}";
  var uid = "{uid}";

  // Base64 → ArrayBuffer
  function b64ToAB(b64){{
    var bin = atob(b64), ab = new ArrayBuffer(bin.length),
        u8 = new Uint8Array(ab);
    for(var i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
    return ab;
  }}

  // バイナリSTL解析
  function parseBinarySTL(ab){{
    var dv = new DataView(ab), geo = {{}};
    var nTri = dv.getUint32(80, true);
    var pos = [], norm = [];
    var off = 84;
    for(var i=0;i<nTri;i++){{
      var nx=dv.getFloat32(off,true),
          ny=dv.getFloat32(off+4,true),
          nz=dv.getFloat32(off+8,true);
      off+=12;
      for(var v=0;v<3;v++){{
        pos.push(dv.getFloat32(off,true),
                 dv.getFloat32(off+4,true),
                 dv.getFloat32(off+8,true));
        norm.push(nx,ny,nz);
        off+=12;
      }}
      off+=2;
    }}
    geo.positions = new Float32Array(pos);
    geo.normals   = new Float32Array(norm);
    return geo;
  }}

  function loadThree(){{
    if(window.THREE && THREE.WebGLRenderer){{ initScene(); return; }}
    var s=document.createElement('script');
    s.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    s.onload=initScene;
    s.onerror=function(){{
      var e=document.getElementById('err_'+uid);
      e.textContent='Three.js の読み込みに失敗しました（オフライン環境では動作しません）';
      e.style.display='block';
    }};
    document.head.appendChild(s);
  }}

  function initScene(){{
    var canvas = document.getElementById('c_'+uid);
    if(!canvas) return;
    var W = canvas.clientWidth || 700, H = canvas.clientHeight || 420;
    canvas.width = W; canvas.height = H;

    var renderer = new THREE.WebGLRenderer({{canvas:canvas, antialias:true, alpha:true}});
    renderer.setPixelRatio(window.devicePixelRatio||1);
    renderer.setSize(W, H);
    renderer.shadowMap.enabled = true;

    var scene  = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, W/H, 0.01, 10000);

    // ライティング
    scene.add(new THREE.AmbientLight(0xffffff, 0.45));
    var dl = new THREE.DirectionalLight(0xffffff, 0.85);
    dl.position.set(1, 2, 3);
    scene.add(dl);
    var dl2 = new THREE.DirectionalLight(0x8888ff, 0.3);
    dl2.position.set(-2, -1, -1);
    scene.add(dl2);

    // STL読み込み
    var ab  = b64ToAB(STL_B64);
    var geo_data = parseBinarySTL(ab);
    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(geo_data.positions, 3));
    geo.setAttribute('normal',   new THREE.BufferAttribute(geo_data.normals,   3));

    var mat = new THREE.MeshPhongMaterial({{
      color: 0x4a90d9, specular: 0x222244,
      shininess: 60, side: THREE.DoubleSide
    }});
    var mesh = new THREE.Mesh(geo, mat);

    // ワイヤーフレーム
    var wmat = new THREE.MeshBasicMaterial({{
      color: 0x88bbff, wireframe: true, opacity: 0.08, transparent: true
    }});
    mesh.add(new THREE.Mesh(geo, wmat));
    scene.add(mesh);

    // グリッド（モデルサイズに合わせたサイズ）
    var gridSz = Math.ceil(sz * 3 / 10) * 10;
    var grid = new THREE.GridHelper(gridSz, 20, 0x334455, 0x223344);
    grid.material.opacity = 0.4; grid.material.transparent = true;
    scene.add(grid);

    // バウンディングボックスからモデルを原点中心に配置
    geo.computeBoundingBox();
    var bb = geo.boundingBox;
    var cx = (bb.max.x+bb.min.x)/2,
        cy = (bb.max.y+bb.min.y)/2,
        cz = (bb.max.z+bb.min.z)/2;
    var dx = bb.max.x-bb.min.x,
        dy = bb.max.y-bb.min.y,
        dz = bb.max.z-bb.min.z;
    var sz = Math.max(dx, dy, dz) || 1;
    // モデルを原点中心へ移動
    mesh.position.set(-cx, -cz, cy);   // STL座標(X,Y,Z) → Three.js(X,Z,-Y)
    grid.position.y = -(dz/2 + 2);
    // カメラ初期位置
    var dist0 = sz * 2.2;

    // マウス操作
    var drag=false, rclick=false,
        ox=0, oy=0,
        rotX=0.4, rotY=0.6, dist=dist0,
        panX=0, panY=0;

    canvas.addEventListener('mousedown', function(e){{
      if(e.button===2) rclick=true; else drag=true;
      ox=e.clientX; oy=e.clientY; e.preventDefault();
    }});
    canvas.addEventListener('contextmenu', function(e){{e.preventDefault();}});
    window.addEventListener('mouseup', function(){{drag=false;rclick=false;}});
    window.addEventListener('mousemove', function(e){{
      var dx=e.clientX-ox, dy=e.clientY-oy; ox=e.clientX; oy=e.clientY;
      if(drag){{ rotY+=dx*0.008; rotX+=dy*0.008; }}
      if(rclick){{ panX+=dx*dist*0.001; panY-=dy*dist*0.001; }}
    }});
    canvas.addEventListener('wheel', function(e){{
      dist *= (e.deltaY>0)?1.12:0.89; e.preventDefault();
    }},{{passive:false}});

    // タッチ操作（スマホ対応）
    var touches={{}}, pinchDist0=0;
    canvas.addEventListener('touchstart',function(e){{
      for(var t of e.touches) touches[t.identifier]={{x:t.clientX,y:t.clientY}};
      if(e.touches.length===2){{
        var a=e.touches[0],b=e.touches[1];
        pinchDist0=Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);
      }}
      e.preventDefault();
    }},{{passive:false}});
    canvas.addEventListener('touchmove',function(e){{
      if(e.touches.length===1){{
        var t=e.touches[0], prev=touches[t.identifier]||{{x:t.clientX,y:t.clientY}};
        rotY+=(t.clientX-prev.x)*0.01; rotX+=(t.clientY-prev.y)*0.01;
        touches[t.identifier]={{x:t.clientX,y:t.clientY}};
      }} else if(e.touches.length===2){{
        var a=e.touches[0],b=e.touches[1];
        var d=Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY);
        dist*=pinchDist0/d; pinchDist0=d;
      }}
      e.preventDefault();
    }},{{passive:false}});

    function animate(){{
      requestAnimationFrame(animate);
      var x=Math.cos(rotX)*Math.sin(rotY)*dist,
          y=Math.sin(rotX)*dist,
          z=Math.cos(rotX)*Math.cos(rotY)*dist;
      camera.position.set(x+panX, y+panY, z);
      camera.lookAt(panX, panY, 0);
      renderer.render(scene, camera);
    }}
    animate();

    // リサイズ対応
    var ro = new ResizeObserver(function(){{
      var W2=canvas.clientWidth, H2=canvas.clientHeight;
      renderer.setSize(W2,H2); camera.aspect=W2/H2; camera.updateProjectionMatrix();
    }});
    ro.observe(canvas);
  }}

  loadThree();
}})();
</script>"""

    def _find_latest_stl(code):
        """実行コードからSTLパスを抽出し、ノートブックのcwdを基準に絶対パスで返す"""
        import re
        cwd = os.getcwd()
        hits = re.findall(r"export_stl\s*\([^,]+,\s*['\"]([^'\"]+\.stl)['\"]", code)
        candidates = hits if hits else []
        # フォールバック: output/ 以下で最新
        out_dir = os.path.join(cwd, 'output')
        if os.path.isdir(out_dir):
            stls = []
            for fn in os.listdir(out_dir):
                if fn.endswith('.stl'):
                    fp = os.path.join(out_dir, fn)
                    stls.append((os.path.getmtime(fp), fp))
            if stls:
                candidates.append(sorted(stls)[-1][1])
        # candidates を絶対パスに解決して存在確認
        for c in reversed(candidates):
            p = c if os.path.isabs(c) else os.path.join(cwd, c)
            if os.path.exists(p):
                return p
        return None

    def _show_viewer(stl_path, out_widget):
        """生成後に out_widget にビューアを表示する"""
        if not stl_path or not os.path.exists(stl_path):
            with out_widget:
                print(f"⚠️ STLが見つかりません: {stl_path}")
            return
        try:
            html = _make_viewer_html(stl_path)
            with out_widget:
                display(HTML(html))
        except Exception as e:
            with out_widget:
                print(f"⚠️ ビューア生成エラー: {e}")


    # ── サンプルタブのウィジェット構築ヘルパー ────────────────
    sample_log_out    = w.Output()
    sample_code_out   = w.Output()
    sample_viewer_out = w.Output()

    def _run_sample(code, label):
        import ast as _ast, traceback as _tb
        sample_log_out.clear_output()
        sample_code_out.clear_output()
        sample_viewer_out.clear_output()
        with sample_code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))
        with sample_log_out:
            print(f'▶ {label} を実行中...')
        try:
            _ast.parse(code)
            exec(compile(code, '<sample>', 'exec'), {'__builtins__': __builtins__})
            with sample_log_out:
                print('✅ 生成完了！  output/ フォルダを確認してください。')
            stl = _find_latest_stl(code)
            if stl:
                _show_viewer(stl, sample_viewer_out)
        except Exception:
            with sample_log_out:
                print('❌ エラー:\n' + _tb.format_exc())

    def _make_sample_row(s):
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

    sample_tab = w.VBox([
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

    # ══════════════════════════════════════════════════════════════
    # ⚙️ 機械部品タブ（パラメータGUI付き）
    # ══════════════════════════════════════════════════════════════
    mech_log_out    = w.Output()
    mech_code_out   = w.Output()
    mech_viewer_out = w.Output()

    def _run_mech(code, label):
        import ast as _ast, traceback as _tb
        mech_log_out.clear_output()
        mech_code_out.clear_output()
        mech_viewer_out.clear_output()
        with mech_code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))
        with mech_log_out:
            print(f'▶ {label} を実行中...')
        try:
            _ast.parse(code)
            exec(compile(code, '<mech>', 'exec'), {'__builtins__': __builtins__})
            with mech_log_out:
                print('✅ 生成完了！  output/ フォルダを確認してください。')
            stl = _find_latest_stl(code)
            if stl:
                _show_viewer(stl, mech_viewer_out)
        except Exception:
            with mech_log_out:
                print('❌ エラー:\n' + _tb.format_exc())

    def _slider(desc, val, mn, mx, step, unit='mm'):
        label = w.Label(f'{desc}:', layout=w.Layout(width='160px'))
        sl = w.FloatSlider(value=val, min=mn, max=mx, step=step,
                           readout_format='.1f',
                           layout=w.Layout(width='260px'))
        unit_l = w.Label(unit, layout=w.Layout(width='36px'))
        return w.HBox([label, sl, unit_l]), sl

    def _int_slider(desc, val, mn, mx, unit=''):
        label = w.Label(f'{desc}:', layout=w.Layout(width='160px'))
        sl = w.IntSlider(value=val, min=mn, max=mx,
                         layout=w.Layout(width='260px'))
        unit_l = w.Label(unit, layout=w.Layout(width='36px'))
        return w.HBox([label, sl, unit_l]), sl

    def _section(title):
        return w.HTML(f'<div style="font-size:14px;font-weight:700;'
                      f'margin:12px 0 6px;border-bottom:2px solid #4a90d9;'
                      f'padding-bottom:4px;color:#1a3a5c">{title}</div>')

    # ── ① 平歯車（スパーギア） ──────────────────────────────
    _sg_title = _section('⚙️ ① 平歯車（スパーギア）')
    _sg_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                     'インボリュート歯形を BuildSketch + spline で近似生成。'
                     'モジュール・歯数・歯幅を調整できます。</div>')
    (_sg_r1, sg_module)   = _slider('モジュール m',    2.0,  0.5, 5.0, 0.5, 'mm')
    (_sg_r2, sg_teeth)    = _int_slider('歯数 z',       20,   8,  60, '枚')
    (_sg_r3, sg_width)    = _slider('歯幅 b',          15.0,  5.0, 50.0, 1.0, 'mm')
    (_sg_r4, sg_press)    = _slider('圧力角 α',        20.0, 14.5, 25.0, 0.5, '°')
    (_sg_r5, sg_hub_d)    = _slider('ハブ径',          10.0,  0.0, 30.0, 1.0, 'mm')
    (_sg_r6, sg_key_w)    = _slider('キー溝幅',         0.0,  0.0, 10.0, 0.5, 'mm')
    sg_btn = w.Button(description='▶ 歯車を生成', button_style='primary',
                      layout=w.Layout(width='150px', margin='8px 0'))

    def _build_spur_gear_code():
        m   = sg_module.value
        z   = sg_teeth.value
        b   = sg_width.value
        pa  = sg_press.value
        hd  = sg_hub_d.value
        kw  = sg_key_w.value
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
        Polygon([Vector(x, y) for x, y in all_pts], align=None)
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
print(f'✅ 平歯車 m={{m}} z={{z}} b={{b}}mm')
print(f'   基準円径: {{m*z:.2f}}mm  歯先円径: {{ra*2:.2f}}mm')
print(f'   → output/spur_gear.step / .stl')
"""

    def _on_sg(b):
        sg_btn.disabled = True; sg_btn.description = '実行中...'
        _run_mech(_build_spur_gear_code(), '平歯車')
        sg_btn.disabled = False; sg_btn.description = '▶ 歯車を生成'

    sg_btn.on_click(_on_sg)

    spur_gear_panel = w.VBox([
        _sg_title, _sg_tip,
        _sg_r1, _sg_r2, _sg_r3, _sg_r4, _sg_r5, _sg_r6,
        sg_btn,
    ])

    # ── ② 六角ボルト ────────────────────────────────────────
    _bolt_title = _section('🔩 ② 六角ボルト（JIS 準拠形状）')
    _bolt_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                       '軸径・首下長・ねじピッチ・頭部サイズを調整。'
                       'ねじ山は螺旋スイープで立体的に生成します。</div>')
    (_b1, bolt_d)      = _slider('軸径 d',         8.0,  3.0, 24.0, 1.0, 'mm')
    (_b2, bolt_len)    = _slider('首下長 L',        40.0, 5.0,150.0, 5.0, 'mm')
    (_b3, bolt_pitch)  = _slider('ピッチ p',         1.25, 0.5,  4.0, 0.25,'mm')
    (_b4, bolt_head_h) = _slider('頭部高さ',         5.0,  2.0, 20.0, 0.5, 'mm')
    (_b5, bolt_key_s)  = _slider('二面幅 (対辺)',    13.0,  6.0, 46.0, 1.0, 'mm')
    (_b6, bolt_thread_d)= _slider('ねじ深さ (対D比)',  0.6,  0.3,  0.9, 0.05,'×d')
    bolt_btn = w.Button(description='▶ ボルトを生成', button_style='primary',
                        layout=w.Layout(width='150px', margin='8px 0'))

    def _build_bolt_code():
        d  = bolt_d.value
        L  = bolt_len.value
        p  = bolt_pitch.value
        hh = bolt_head_h.value
        ks = bolt_key_s.value
        td = bolt_thread_d.value
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
        Polygon([Vector(x, z) for x, z in profile_pts], align=None)
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
print(f'✅ 六角ボルト M{{d:.0f}}×{{L:.0f}}  p={{pitch}}mm')
print(f'   頭部高: {{head_h}}mm  二面幅: {{key_s}}mm')
print(f'   → output/hex_bolt.step / .stl')
"""

    def _on_bolt(b):
        bolt_btn.disabled = True; bolt_btn.description = '実行中...'
        _run_mech(_build_bolt_code(), '六角ボルト')
        bolt_btn.disabled = False; bolt_btn.description = '▶ ボルトを生成'

    bolt_btn.on_click(_on_bolt)

    bolt_panel = w.VBox([
        _bolt_title, _bolt_tip,
        _b1, _b2, _b3, _b4, _b5, _b6,
        bolt_btn,
    ])

    # ── ③ 六角ナット ────────────────────────────────────────
    _nut_title = _section('🔧 ③ 六角ナット（JIS 準拠形状）')
    _nut_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                      '呼び径・ナット高さ・二面幅を調整。'
                      '内部ねじ山も螺旋スイープで立体生成します。</div>')
    (_n1, nut_d)     = _slider('呼び径 d',        8.0,  3.0, 24.0, 1.0, 'mm')
    (_n2, nut_h)     = _slider('ナット高さ H',     6.5,  2.0, 20.0, 0.5, 'mm')
    (_n3, nut_key)   = _slider('二面幅 (対辺)',   13.0,  6.0, 46.0, 1.0, 'mm')
    (_n4, nut_pitch) = _slider('ピッチ p',         1.25, 0.5,  4.0, 0.25,'mm')
    nut_btn = w.Button(description='▶ ナットを生成', button_style='primary',
                       layout=w.Layout(width='150px', margin='8px 0'))

    def _build_nut_code():
        d  = nut_d.value
        H  = nut_h.value
        ks = nut_key.value
        p  = nut_pitch.value
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

    def _on_nut(b):
        nut_btn.disabled = True; nut_btn.description = '実行中...'
        _run_mech(_build_nut_code(), '六角ナット')
        nut_btn.disabled = False; nut_btn.description = '▶ ナットを生成'

    nut_btn.on_click(_on_nut)

    nut_panel = w.VBox([
        _nut_title, _nut_tip,
        _n1, _n2, _n3, _n4,
        nut_btn,
    ])

    # ── ④ 深溝玉軸受（ベアリング） ──────────────────────────
    _brg_title = _section('🎯 ④ 深溝玉軸受（ボールベアリング）')
    _brg_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                      '内輪・外輪・ボール・保持器を個別に生成。'
                      'JIS 呼び番号に近いサイズで調整できます。</div>')
    (_br1, brg_id)     = _slider('内径 d',         20.0, 5.0, 80.0, 1.0, 'mm')
    (_br2, brg_od)     = _slider('外径 D',         47.0,15.0,120.0, 1.0, 'mm')
    (_br3, brg_width)  = _slider('幅 B',           14.0, 3.0, 30.0, 0.5, 'mm')
    (_br4, brg_balls)  = _int_slider('ボール数',     8,   4,  20, '個')
    (_br5, brg_ball_d) = _slider('ボール径',         6.5, 2.0, 20.0, 0.5, 'mm')
    brg_btn = w.Button(description='▶ ベアリングを生成', button_style='primary',
                       layout=w.Layout(width='160px', margin='8px 0'))

    def _build_bearing_code():
        di = brg_id.value
        do = brg_od.value
        bw = brg_width.value
        nb = brg_balls.value
        bd = brg_ball_d.value
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

print(f'✅ 深溝玉軸受  内径{{inner_d}}×外径{{outer_d}}×幅{{width}}mm')
print(f'   ボール {{n_balls}}個 φ{{ball_d}}mm')
print(f'   → output/bearing_*.step / .stl（外輪・内輪・ボール・保持器）')
"""

    def _on_brg(b):
        brg_btn.disabled = True; brg_btn.description = '実行中...'
        _run_mech(_build_bearing_code(), '深溝玉軸受')
        brg_btn.disabled = False; brg_btn.description = '▶ ベアリングを生成'

    brg_btn.on_click(_on_brg)

    bearing_panel = w.VBox([
        _brg_title, _brg_tip,
        _br1, _br2, _br3, _br4, _br5,
        brg_btn,
    ])

    # ── ⑤ パイプ継手（エルボ） ──────────────────────────────
    _elbow_title = _section('🔄 ⑤ パイプ継手（エルボ / スイープ）')
    _elbow_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                        '円弧パス上に環状断面をスイープ。'
                        '曲がり角度・パイプ径・肉厚を自由に設定できます。</div>')
    (_el1, elbow_od)    = _slider('外径 D',         42.0, 10.0,120.0, 2.0, 'mm')
    (_el2, elbow_t)     = _slider('肉厚 t',          3.5,  1.0, 15.0, 0.5, 'mm')
    (_el3, elbow_r)     = _slider('曲率半径 R',      60.0, 20.0,200.0, 5.0, 'mm')
    (_el4, elbow_angle) = _slider('曲がり角度 θ',    90.0, 15.0,180.0, 5.0, '°')
    (_el5, elbow_ext)   = _slider('直管延長',         20.0,  0.0, 80.0, 5.0, 'mm')
    elbow_btn = w.Button(description='▶ 継手を生成', button_style='primary',
                         layout=w.Layout(width='150px', margin='8px 0'))

    def _build_elbow_code():
        od    = elbow_od.value
        t     = elbow_t.value
        R     = elbow_r.value
        angle = elbow_angle.value
        ext   = elbow_ext.value
        return f"""\
from build123d import *
import os, math
os.makedirs('output', exist_ok=True)

outer_d = {od}    # 外径 [mm]
wall_t  = {t}     # 肉厚 [mm]
bend_R  = {R}     # 曲率半径 [mm]
angle   = {angle} # 曲がり角度 [°]
ext_len = {ext}   # 直管延長 [mm]

ro = outer_d / 2
ri = ro - wall_t

with BuildPart() as elbow:
    # ── 曲がり部（CenterArc スイープ）──
    path = CenterArc(
        center=(bend_R, 0),
        radius=bend_R,
        start_angle=180,
        arc_size=-angle
    )
    with BuildSketch(
        Plane(origin=path.start_location.position,
              z_dir=path.start_location.z_axis)
    ) as sk_pipe:
        Circle(ro)
        Circle(ri, mode=Mode.SUBTRACT)
    sweep(path=path)

    # ── 直管（入口側）──
    if ext_len > 0:
        start_pos = path.start_location.position
        start_dir = path.start_location.z_axis
        with BuildSketch(Plane(origin=start_pos, z_dir=start_dir)) as sk_ext1:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

    # ── 直管（出口側）──
    if ext_len > 0:
        end_pos = path.end_location.position
        end_dir = path.end_location.z_axis
        with BuildSketch(Plane(origin=end_pos, z_dir=end_dir)) as sk_ext2:
            Circle(ro)
            Circle(ri, mode=Mode.SUBTRACT)
        extrude(amount=ext_len)

export_step(elbow.part, 'output/pipe_elbow.step')
export_stl(elbow.part,  'output/pipe_elbow.stl')
print(f'✅ パイプ継手 φ{{outer_d}}×t{{wall_t}} R={{bend_R}}mm {{angle}}°')
print(f'   → output/pipe_elbow.step / .stl')
"""

    def _on_elbow(b):
        elbow_btn.disabled = True; elbow_btn.description = '実行中...'
        _run_mech(_build_elbow_code(), 'パイプ継手')
        elbow_btn.disabled = False; elbow_btn.description = '▶ 継手を生成'

    elbow_btn.on_click(_on_elbow)

    elbow_panel = w.VBox([
        _elbow_title, _elbow_tip,
        _el1, _el2, _el3, _el4, _el5,
        elbow_btn,
    ])

    # ── ⑥ Vプーリー ─────────────────────────────────────────
    _pulley_title = _section('🔘 ⑥ Vプーリー（ロフト溝）')
    _pulley_tip = w.HTML('<div class="cad-tip" style="margin-bottom:6px">'
                         'Vベルト用の溝形状を BuildSketch + revolve で生成。'
                         '溝数・プーリー径・V角度を変更できます。</div>')
    (_pl1, pulley_od)    = _slider('外径 D',       100.0, 30.0,300.0, 5.0, 'mm')
    (_pl2, pulley_hub)   = _slider('ハブ径',         25.0,  8.0, 60.0, 1.0, 'mm')
    (_pl3, pulley_width) = _slider('プーリー幅',     40.0, 10.0,120.0, 2.0, 'mm')
    (_pl4, pulley_grooves)= _int_slider('溝数',      2,    1,   6, '本')
    (_pl5, pulley_v_angle)= _slider('V角度 (片側)', 17.0,  8.0, 25.0, 1.0, '°')
    (_pl6, pulley_groove_d)= _slider('溝深さ',        8.0,  3.0, 20.0, 0.5, 'mm')
    pulley_btn = w.Button(description='▶ プーリーを生成', button_style='primary',
                          layout=w.Layout(width='160px', margin='8px 0'))

    def _build_pulley_code():
        od  = pulley_od.value
        hd  = pulley_hub.value
        pw  = pulley_width.value
        ng  = pulley_grooves.value
        va  = pulley_v_angle.value
        gd  = pulley_groove_d.value
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
            Polygon(pts, align=None)
        revolve(axis=Axis.Z, revolution_arc=360, mode=Mode.SUBTRACT)

export_step(pulley.part, 'output/v_pulley.step')
export_stl(pulley.part,  'output/v_pulley.stl')
print(f'✅ Vプーリー φ{{outer_d}} 幅{{pwidth}}mm {{n_grooves}}溝')
print(f'   → output/v_pulley.step / .stl')
"""

    def _on_pulley(b):
        pulley_btn.disabled = True; pulley_btn.description = '実行中...'
        _run_mech(_build_pulley_code(), 'Vプーリー')
        pulley_btn.disabled = False; pulley_btn.description = '▶ プーリーを生成'

    pulley_btn.on_click(_on_pulley)

    pulley_panel = w.VBox([
        _pulley_title, _pulley_tip,
        _pl1, _pl2, _pl3, _pl4, _pl5, _pl6,
        pulley_btn,
    ])

    # ── 機械部品タブ組立 ────────────────────────────────────
    mech_accordion = w.Accordion(children=[
        spur_gear_panel, bolt_panel, nut_panel,
        bearing_panel, elbow_panel, pulley_panel,
    ])
    for i, title in enumerate([
        '⚙️ ① 平歯車（スパーギア）',
        '🔩 ② 六角ボルト',
        '🔧 ③ 六角ナット',
        '🎯 ④ 深溝玉軸受（ベアリング）',
        '🔄 ⑤ パイプ継手（エルボ）',
        '🔘 ⑥ Vプーリー',
    ]):
        mech_accordion.set_title(i, title)
    mech_accordion.selected_index = 0

    mech_tab = w.VBox([
        w.HTML('<div style="font-size:13px;color:#555;margin-bottom:8px">'
               'アコーディオンで部品を選び、パラメータを調整して ▶ 生成 ボタンを押してください。<br>'
               'STEP / STL が <code>output/</code> に保存されます。</div>'),
        mech_accordion,
        w.HTML('<hr style="margin:10px 0"><b>実行ログ</b>'),
        mech_log_out,
        w.HTML('<b>🖥️ 3Dビューア</b>'),
        mech_viewer_out,
        w.HTML('<b>実行コード</b>'),
        mech_code_out,
    ], layout=w.Layout(padding='10px'))

    # ── ダッシュボード組立 ────────────────────────────────────
    tabs = w.Tab(children=[settings_tab, api_tab, manual_tab, sample_tab, mech_tab, hist_tab])
    tabs.set_title(0, '⚙️ API設定')
    tabs.set_title(1, '🤖 API 自動生成')
    tabs.set_title(2, '📋 Manual')
    tabs.set_title(3, '🔬 サンプル')
    tabs.set_title(4, '🔩 機械部品')
    tabs.set_title(5, '📜 会話履歴')

    dashboard = w.VBox([
        w.HTML('<h3 style="margin:4px 0 8px">🔧 Build123d × LLM ダッシュボード</h3>'),
        tabs,
    ], layout=w.Layout(padding='8px'))

    display(dashboard)
    print('✅ GUI 起動完了  ─  まず「⚙️ API設定」タブでモードとキーを設定してください')
