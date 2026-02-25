"""
gui/utils/code_utils.py
────────────────
コード抽出・検証・安全性チェック・自動パッチ・実行ユーティリティ。
"""
from typing import Tuple, List
from gui.state import BANNED

def extract_code(text: str) -> str:
    """
    テキストからPythonコードブロックのみを抽出して返す。
    """
    import re
    code_blocks = re.findall(r'```(?:python)?\s*([\s\S]+?)```', text)
    if code_blocks:
        return code_blocks[0].strip()
    return text.strip()

def validate_code_block(code: str, raw_response: str) -> Tuple[bool, str]:
    """
    コードブロックが有効かどうかを検証し、エラーメッセージを返す。
    """
    if not code.strip():
        return False, 'コードが空です。'
    if any(b in code for b in BANNED):
        return False, '禁止ワードが含まれています。'
    if '```' in raw_response and code not in raw_response:
        return False, 'コードブロック抽出に失敗しました。'
    return True, ''

def safety_check(code: str) -> List[str]:
    """
    禁止ワードが含まれていないかチェックし、違反ワード一覧を返す。
    """
    return [b for b in BANNED if b in code]

def auto_patch(code: str) -> Tuple[str, List[str]]:
    """
    コードの安全性を自動修正（禁止ワード除去）し、修正後コードと除去ワード一覧を返す。
    """
    removed = [b for b in BANNED if b in code]
    patched = code
    for b in removed:
        patched = patched.replace(b, '')
    return patched, removed

def run_code(code: str) -> Tuple[bool, str]:
    """
    コードをexecで実行し、成功可否と出力またはエラーを返す。
    """
    import io
    import contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {})
        return True, buf.getvalue()
    except Exception as e:
        return False, str(e)
