"""
gui/tabs/__init__.py
────────────────
タブ生成関数のインポート。
"""
from .api_settings_tab import create_api_settings_tab
from .auto_generation_tab import create_auto_generation_tab
from .manual_tab import create_manual_tab
from .samples_tab import create_samples_tab
from .history_tab import create_history_tab
from .machine_parts import create_machine_parts_tab
