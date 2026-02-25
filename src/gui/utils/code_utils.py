"""
gui/utils/code_utils.py
────────────────
コード抽出・検証・安全チェック・自動修正・実行ユーティリティ群。
"""
import re
import ast
import traceback
from typing import Tuple, Any
from gui.state import BANNED

def extract_code(text: str) -> str:
    """LLMの返答からPythonコードブロックを確実に抽出する。"""
    m = re.search(r'```(?:python)?[ \t]*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'(from build123d import.*)', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ''

def validate_code_block(code: str, raw_response: str) -> Tuple[bool, str]:
    """コードブロックの基本的な妥当性を検証する。"""
    if not code:
        return False, (
            'LLMがコードブロックを返しませんでした。\n'
            f'LLMの返答（先頭200文字）:\n{raw_response[:200]}'
        )
    if 'from build123d' not in code and 'BuildPart' not in code:
        return False, (
            'Build123dのコードが含まれていません。\n'
            f'抽出されたテキスト（先頭200文字）:\n{code[:200]}'
        )
    return True, ''

def safety_check(code: str) -> list[str]:
    """禁止パターンを検出して返す。"""
    return [b for b in BANNED if b in code]

def auto_patch(code: str) -> Tuple[str, list[str]]:
    """LLMがよく間違えるパターンを実行前に自動修正する。"""
    patches: list[str] = []

    def fix_method_fillet(m: re.Match) -> str:
        varname = m.group(1)
        args = m.group(2)
        patches.append(f'  {varname}.fillet({args}) → fillet({varname}.edges(), {args})')
        return f'fillet({varname}.edges(), {args})'
    code = re.sub(r'(\w+)\.fillet\(([^)]+)\)', fix_method_fillet, code)

    def fix_method_chamfer(m: re.Match) -> str:
        varname = m.group(1)
        args = m.group(2)
        patches.append(f'  {varname}.chamfer({args}) → chamfer({varname}.edges(), {args})')
        return f'chamfer({varname}.edges(), {args})'
    code = re.sub(r'(\w+)\.chamfer\(([^)]+)\)', fix_method_chamfer, code)

    code = re.sub(r'fillet\((\w+)\.part\.edges\(\)', r'fillet(\1.edges()', code)
    code = re.sub(r'chamfer\((\w+)\.part\.edges\(\)', r'chamfer(\1.edges()', code)

    if '.filter_by_orientation' in code:
        code = re.sub(r'\.filter_by_orientation\([^)]*\)', '', code)
        patches.append('  .filter_by_orientation(...) → 削除（存在しないメソッド）')

    return code, patches

def run_code(code: str) -> Tuple[bool, str, Any]:
    """コードを安全にチェックして実行し、生成されたオブジェクトを返す。"""
    code, patches = auto_patch(code)
    if patches:
        print('🔧 自動修正を適用しました:')
        for p in patches:
            print(p)

    dangers = safety_check(code)
    if dangers:
        return False, f'安全チェックNG: {dangers}', None
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f'構文エラー: {e}', None

    loc = {}
    try:
        # 実行
        exec(compile(code, '<llm_generated>', 'exec'), {'__builtins__': __builtins__}, loc)
        
        # BuildPart オブジェクトを探す
        last_obj = None
        for v in loc.values():
            if hasattr(v, 'part'):
                last_obj = v
        
        return True, '', last_obj
    except Exception:
        return False, traceback.format_exc(), None