"""
gui/tabs/machine_parts/base_panel.py
────────────────
機械部品パネルの共通基底クラス（ocp_cad_viewer 対応版）。
"""
from abc import ABC, abstractmethod
from typing import Tuple
import ipywidgets as w
from IPython.display import display, HTML


class MachinePartPanel(ABC):
    """機械部品パネルの共通基底クラス"""
    title: str
    log_out: w.Output
    viewer_out: w.Output
    code_out: w.Output

    @abstractmethod
    def _build_code(self) -> str:
        """スライダー値から実行コードを組み立てて返す"""
        ...

    @abstractmethod
    def build_widget(self) -> w.VBox:
        """タブに追加するウィジェットを返す"""
        ...

    def _run(self, label: str) -> None:
        """_build_code() を実行し、ログ・ビューア・コードを更新する共通処理"""
        from gui.utils.code_utils import run_code
        from gui.utils.viewer import _show_viewer

        code = self._build_code()
        self.code_out.clear_output()
        self.viewer_out.clear_output()
        self.log_out.clear_output()

        with self.code_out:
            display(HTML(f'<div class="cad-code">{code}</div>'))
        with self.log_out:
            print(f'▶ {label} を生成中...')

        # オブジェクトを受け取るように修正
        ok, err, obj = run_code(code)
        if ok:
            with self.log_out:
                print('✅ 生成完了')
            # 直接表示
            _show_viewer(obj, self.viewer_out)
        else:
            with self.log_out:
                print(f'❌ エラー:\n{err}')

    @staticmethod
    def _slider(
        desc: str, val: float, mn: float, mx: float, step: float, unit: str = 'mm'
    ) -> Tuple[w.HBox, w.FloatSlider]:
        label  = w.Label(f'{desc}:', layout=w.Layout(width='160px'))
        slider = w.FloatSlider(
            value=val, min=mn, max=mx, step=step,
            readout_format='.1f',
            layout=w.Layout(width='260px')
        )
        unit_l = w.Label(unit, layout=w.Layout(width='36px'))
        return w.HBox([label, slider, unit_l]), slider

    @staticmethod
    def _int_slider(
        desc: str, val: int, mn: int, mx: int, unit: str = ''
    ) -> Tuple[w.HBox, w.IntSlider]:
        label  = w.Label(f'{desc}:', layout=w.Layout(width='160px'))
        slider = w.IntSlider(
            value=val, min=mn, max=mx,
            layout=w.Layout(width='260px')
        )
        unit_l = w.Label(unit, layout=w.Layout(width='36px'))
        return w.HBox([label, slider, unit_l]), slider

    @staticmethod
    def _section(title: str) -> w.HTML:
        return w.HTML(
            f'<div style="font-size:14px;font-weight:700;'
            f'margin:12px 0 6px;border-bottom:2px solid #4a90d9;'
            f'padding-bottom:4px;color:#1a3a5c">{title}</div>'
        )