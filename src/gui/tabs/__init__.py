"""
gui/tabs/__init__.py
"""
from .api_settings_tab import create_api_settings_tab
from .auto_generation_tab import create_auto_generation_tab
from .manual_tab import create_manual_tab
from .samples_tab import create_samples_tab
from .machine_parts_tab import create_machine_parts_tab
from .history_tab import create_history_tab

__all__ = [
    'create_api_settings_tab',
    'create_auto_generation_tab',
    'create_manual_tab',
    'create_samples_tab',
    'create_machine_parts_tab',
    'create_history_tab',
]
