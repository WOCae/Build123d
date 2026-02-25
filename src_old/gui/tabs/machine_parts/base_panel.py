"""
gui/tabs/machine_parts/base_panel.py
────────────────
機械部品パネルの共通基底クラス。
"""
from abc import ABC, abstractmethod
from ipywidgets import VBox, Output, Layout, FloatSlider, IntSlider, HTML
from typing import Any

class MachinePartPanel(ABC):
    """機械部品パネルの共通基底クラス"""
    title: str
    log_out: Output
    viewer_out: Output
    code_out: Output

    @abstractmethod
    def _build_code(self) -> str:
        """
        スライダー値から実行コードを組み立てて返す
        """
        ...

    @abstractmethod
    def build_widget(self) -> VBox:
        """
        タブに追加するウィジェットを返す
        """
        ...

    def _run(self, label: str) -> None:
        """
        _build_code() を実行し、ログ・ビューア・コードを更新する共通処理
        """
        code = self._build_code()
        self.code_out.clear_output()
        self.viewer_out.clear_output()
        self.log_out.clear_output()
        with self.code_out:
            print(code)
        # 実際の描画・実行処理は各サブクラスで実装

    @staticmethod
    def _slider(description: str, min_val: float, max_val: float, step: float, value: float, unit: str = "") -> FloatSlider:
        return FloatSlider(
            description=description,
            min=min_val,
            max=max_val,
            step=step,
            value=value,
            readout=True,
            readout_format=f".2f{unit}",
            layout=Layout(width="95%")
        )

    @staticmethod
    def _int_slider(description: str, min_val: int, max_val: int, step: int, value: int, unit: str = "") -> IntSlider:
        return IntSlider(
            description=description,
            min=min_val,
            max=max_val,
            step=step,
            value=value,
            readout=True,
            readout_format=f"d{unit}",
            layout=Layout(width="95%")
        )

    @staticmethod
    def _section(title: str) -> HTML:
        return HTML(f'<b style="font-size:13px">{title}</b>')
