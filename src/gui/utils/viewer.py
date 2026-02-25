"""
gui/utils/viewer.py
────────────────
STLインラインビューア共通ユーティリティ。
"""
import os
import ipywidgets as w
from IPython.display import display, HTML


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
