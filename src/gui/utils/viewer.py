
import os
import ipywidgets as w
from IPython.display import display

def _show_viewer(obj, out_widget):
    out_widget.clear_output()
    if obj is None:
        with out_widget:
            print("⚠️ 表示するオブジェクトがありません。")
        return
    try:
        target = obj.part if hasattr(obj, 'part') else obj
        # VS Code の OCP CAD Viewer にモデルを送信
        from ocp_vscode import show
        show(target)
        with out_widget:
            print("✅ VS Code の「OCP CAD Viewer」タブにモデルを送信しました！")
            print("👉 画面右側（または別タブ）のビューアーを確認してください。")
    except Exception as e:
        with out_widget:
            print(f"⚠️ ocp_vscode 送信エラー: {e}")
            print("💡 VS Code の OCP CAD Viewer 拡張機能が起動しているか確認してください。")

def _find_latest_stl(code): return None
