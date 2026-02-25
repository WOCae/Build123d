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

    # ────────────────────────────────────────────────────────
    # ヘルパー: UIパーツ生成
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _section(title: str) -> w.HTML:
        """セクションタイトルを返す"""
        return w.HTML(
            f'<div style="font-size:14px;font-weight:700;'
            f'border-bottom:2px solid #4f8cff;padding-bottom:4px;'
            f'margin-bottom:8px;margin-top:4px">{title}</div>'
        )

    @staticmethod
    def _slider(
        label: str,
        value: float,
        min_v: float,
        max_v: float,
        step: float,
        unit: str = '',
    ) -> Tuple[w.HBox, w.FloatSlider]:
        """ラベル付き FloatSlider を (HBox, slider) で返す"""
        slider = w.FloatSlider(
            value=value, min=min_v, max=max_v, step=step,
            readout_format='.2f',
            layout=w.Layout(width='320px'),
            style={'description_width': '0px'},
        )
        lbl = w.Label(
            f'{label}',
            layout=w.Layout(width='130px', justify_content='flex-end'),
        )
        unit_lbl = w.Label(unit, layout=w.Layout(width='36px'))
        row = w.HBox(
            [lbl, slider, unit_lbl],
            layout=w.Layout(align_items='center', gap='6px', margin='2px 0'),
        )
        return row, slider

    @staticmethod
    def _int_slider(
        label: str,
        value: int,
        min_v: int,
        max_v: int,
        unit: str = '',
    ) -> Tuple[w.HBox, w.IntSlider]:
        """ラベル付き IntSlider を (HBox, slider) で返す"""
        slider = w.IntSlider(
            value=value, min=min_v, max=max_v, step=1,
            layout=w.Layout(width='320px'),
            style={'description_width': '0px'},
        )
        lbl = w.Label(
            f'{label}',
            layout=w.Layout(width='130px', justify_content='flex-end'),
        )
        unit_lbl = w.Label(unit, layout=w.Layout(width='36px'))
        row = w.HBox(
            [lbl, slider, unit_lbl],
            layout=w.Layout(align_items='center', gap='6px', margin='2px 0'),
        )
        return row, slider

    # ────────────────────────────────────────────────────────
    # 抽象メソッド（各パネルで実装）
    # ────────────────────────────────────────────────────────

    @abstractmethod
    def _build_code(self) -> str:
        """スライダー値から実行コードを組み立てて返す"""
        ...

    @abstractmethod
    def build_widget(self) -> w.VBox:
        """タブに追加するウィジェットを返す"""
        ...

    # ────────────────────────────────────────────────────────
    # 共通: コード生成 → 実行 → ビューア表示
    # ────────────────────────────────────────────────────────

    def _run(self, label: str) -> None:
        import traceback
        from gui.utils.code_utils import run_code
        from gui.utils.viewer import _show_viewer

        # 画面をリセット
        self.log_out.clear_output()
        self.code_out.clear_output()
        self.viewer_out.clear_output()

        try:
            with self.log_out:
                print(f'▶ {label} のコードを生成中...')

            code = self._build_code()

            with self.code_out:
                display(HTML(f'<div class="cad-code">{code}</div>'))

            with self.log_out:
                print(f'▶ {label} を実行中...')

            ok, err, obj = run_code(code)

            self.log_out.clear_output()
            with self.log_out:
                if ok:
                    print('✅ 生成成功！ビューアーに送信します。')
                    _show_viewer(obj, self.viewer_out)
                else:
                    print(f'❌ 【実行エラー】:\n{err}')

        except Exception:
            self.log_out.clear_output()
            with self.log_out:
                print(f'💥 【システムエラー（強制キャッチ）】:\n{traceback.format_exc()}')
