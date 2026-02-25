"""
gui/utils/viewer.py
────────────────
ocp_cad_viewer を使用した 3D 表示ユーティリティ。
"""
import os
import ipywidgets as w
from IPython.display import display, HTML
from ocp_cad_viewer import show_object

def _show_viewer(obj, out_widget):
    """
    BuildPart や BuildSketch 等のオブジェクトを ocp_cad_viewer で表示する。
    """
    out_widget.clear_output()
    with out_widget:
        if obj is None:
            print("⚠️ 表示するオブジェクトが見つかりません。")
            print("💡 コード内で 'with BuildPart() as part:' などが正しく定義されているか確認してください。")
            return
        try:
            # BuildPartオブジェクトから形状(part)を抽出して表示
            # show_object は Jupyter 内で自動的に 3D ビューアをレンダリングします
            target = obj.part if hasattr(obj, 'part') else obj
            show_object(target, label="Generated Model")
        except Exception as e:
            print(f"⚠️ ocp_cad_viewer 表示エラー: {e}")
            print("💡 以下のコマンドでライブラリを更新してください:")
            print("   pip install -q 'websockets>=16.0,<17.0' ocp-cad-viewer")

def _find_latest_stl(code):
    """
    (互換性のために残していますが、ocp_cad_viewer 移行後は直接オブジェクトを使用するため、
    メインの描画パスでは使用されなくなります)
    """
    return None