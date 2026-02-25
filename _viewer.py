"""
_viewer.py ── Three.js を使ったインライン STL ビューア
"""
import base64, os, re
from IPython.display import display, HTML
import ipywidgets as w


def find_latest_stl(code: str) -> str | None:
    """実行コードからSTLパスを抽出し、ノートブックのcwdを基準に絶対パスで返す"""
    cwd = os.getcwd()
    hits = re.findall(r"export_stl\s*\([^,]+,\s*['\"]([^'\"]+\.stl)['\"]", code)
    candidates = list(hits)
    out_dir = os.path.join(cwd, 'output')
    if os.path.isdir(out_dir):
        stls = sorted(
            (os.path.getmtime(os.path.join(out_dir, f)), os.path.join(out_dir, f))
            for f in os.listdir(out_dir) if f.endswith('.stl'))
        if stls:
            candidates.append(stls[-1][1])
    for c in reversed(candidates):
        p = c if os.path.isabs(c) else os.path.join(cwd, c)
        if os.path.exists(p):
            return p
    return None


def make_viewer_html(stl_path: str) -> str:
    with open(stl_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    fname = os.path.basename(stl_path)
    uid   = f'v{abs(hash(stl_path)) % 99999:05d}'
    return f"""
<div style="width:100%;max-width:700px;margin:8px 0">
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
  var B64="{b64}", uid="{uid}";
  function b64AB(b){{
    var s=atob(b),ab=new ArrayBuffer(s.length),u=new Uint8Array(ab);
    for(var i=0;i<s.length;i++) u[i]=s.charCodeAt(i); return ab;
  }}
  function parseSTL(ab){{
    var dv=new DataView(ab),n=dv.getUint32(80,true),p=[],nm=[],off=84;
    for(var i=0;i<n;i++){{
      var nx=dv.getFloat32(off,true),ny=dv.getFloat32(off+4,true),nz=dv.getFloat32(off+8,true);
      off+=12;
      for(var v=0;v<3;v++){{
        p.push(dv.getFloat32(off,true),dv.getFloat32(off+4,true),dv.getFloat32(off+8,true));
        nm.push(nx,ny,nz); off+=12;
      }}
      off+=2;
    }}
    return {{pos:new Float32Array(p),norm:new Float32Array(nm)}};
  }}
  function init(){{
    var cv=document.getElementById('c_'+uid);
    if(!cv) return;
    var W=cv.clientWidth||700,H=cv.clientHeight||420;
    cv.width=W; cv.height=H;
    var R=new THREE.WebGLRenderer({{canvas:cv,antialias:true,alpha:true}});
    R.setPixelRatio(devicePixelRatio||1); R.setSize(W,H);
    var S=new THREE.Scene(), C=new THREE.PerspectiveCamera(45,W/H,0.01,100000);
    S.add(new THREE.AmbientLight(0xffffff,0.45));
    [[[1,2,3],0xffffff,0.85],[[-2,-1,-1],0x8888ff,0.3]].forEach(function(d){{
      var l=new THREE.DirectionalLight(d[1],d[2]); l.position.set.apply(l.position,d[0]); S.add(l);
    }});
    var d=parseSTL(b64AB(B64)), g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(d.pos,3));
    g.setAttribute('normal',  new THREE.BufferAttribute(d.norm,3));
    var mesh=new THREE.Mesh(g,new THREE.MeshPhongMaterial({{color:0x4a90d9,specular:0x222244,shininess:60,side:THREE.DoubleSide}}));
    mesh.add(new THREE.Mesh(g,new THREE.MeshBasicMaterial({{color:0x88bbff,wireframe:true,opacity:0.08,transparent:true}})));
    S.add(mesh);
    g.computeBoundingBox();
    var bb=g.boundingBox,
        cx=(bb.max.x+bb.min.x)/2,cy=(bb.max.y+bb.min.y)/2,cz=(bb.max.z+bb.min.z)/2,
        sz=Math.max(bb.max.x-bb.min.x,bb.max.y-bb.min.y,bb.max.z-bb.min.z)||1;
    mesh.position.set(-cx,-cz,cy);
    var grid=new THREE.GridHelper(Math.ceil(sz*3/10)*10,20,0x334455,0x223344);
    grid.material.opacity=0.4; grid.material.transparent=true;
    grid.position.y=-((bb.max.z-bb.min.z)/2+2); S.add(grid);
    var dist=sz*2.2,rotX=0.4,rotY=0.6,panX=0,panY=0,drag=false,rcl=false,ox=0,oy=0;
    cv.addEventListener('mousedown',function(e){{if(e.button===2)rcl=true;else drag=true;ox=e.clientX;oy=e.clientY;e.preventDefault();}});
    cv.addEventListener('contextmenu',function(e){{e.preventDefault();}});
    addEventListener('mouseup',function(){{drag=false;rcl=false;}});
    addEventListener('mousemove',function(e){{
      var dx=e.clientX-ox,dy=e.clientY-oy;ox=e.clientX;oy=e.clientY;
      if(drag){{rotY+=dx*0.008;rotX+=dy*0.008;}}
      if(rcl){{panX+=dx*dist*0.001;panY-=dy*dist*0.001;}}
    }});
    cv.addEventListener('wheel',function(e){{dist*=(e.deltaY>0)?1.12:0.89;e.preventDefault();}},{{passive:false}});
    var tc={{}},pd=0;
    cv.addEventListener('touchstart',function(e){{
      for(var t of e.touches)tc[t.identifier]={{x:t.clientX,y:t.clientY}};
      if(e.touches.length===2)pd=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
      e.preventDefault();
    }},{{passive:false}});
    cv.addEventListener('touchmove',function(e){{
      if(e.touches.length===1){{var t=e.touches[0],pv=tc[t.identifier]||{{x:t.clientX,y:t.clientY}};rotY+=(t.clientX-pv.x)*0.01;rotX+=(t.clientY-pv.y)*0.01;tc[t.identifier]={{x:t.clientX,y:t.clientY}};}}
      else if(e.touches.length===2){{var nd=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);dist*=pd/nd;pd=nd;}}
      e.preventDefault();
    }},{{passive:false}});
    (function frame(){{
      requestAnimationFrame(frame);
      var x=Math.cos(rotX)*Math.sin(rotY)*dist,y=Math.sin(rotX)*dist,z=Math.cos(rotX)*Math.cos(rotY)*dist;
      C.position.set(x+panX,y+panY,z); C.lookAt(panX,panY,0); R.render(S,C);
    }})();
    new ResizeObserver(function(){{var W2=cv.clientWidth,H2=cv.clientHeight;R.setSize(W2,H2);C.aspect=W2/H2;C.updateProjectionMatrix();}}).observe(cv);
  }}
  if(window.THREE&&THREE.WebGLRenderer){{init();}}
  else{{
    var s=document.createElement('script');
    s.src='https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    s.onload=init;
    s.onerror=function(){{var e=document.getElementById('err_'+uid);e.textContent='Three.js の読み込みに失敗しました';e.style.display='block';}};
    document.head.appendChild(s);
  }}
}})();
</script>"""


def show_viewer(stl_path: str | None, out: w.Output) -> None:
    if not stl_path or not os.path.exists(stl_path):
        with out: print(f'⚠️ STLが見つかりません: {stl_path}')
        return
    try:
        with out: display(HTML(make_viewer_html(stl_path)))
    except Exception as e:
        with out: print(f'⚠️ ビューア生成エラー: {e}')
