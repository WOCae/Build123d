"""
gui/utils/deps.py
────────────────
依存ライブラリの自動インストール関数。
"""
from typing import NoneType

def _ensure_deps() -> None:
    """
    必要な依存ライブラリが未インストールの場合は自動でインストールする。
    Jupyter環境でのみ動作を想定。
    """
    import sys
    import subprocess
    import importlib
    required = [
        'ipywidgets', 'IPython', 'requests', 'tqdm', 'nest_asyncio',
        'openai', 'google-generativeai', 'anthropic', 'build123d',
        'numpy', 'scipy', 'matplotlib', 'pandas', 'pythreejs', 'jupyterlab_widgets'
    ]
    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            print(f"[deps] Installing: {pkg}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
