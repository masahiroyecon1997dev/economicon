"""フィクスチャのインデントを修正"""
from pathlib import Path
import re

test_dir = Path('tests')


def fix_fixture_indent(content):
    """フィクスチャ内のインデントを修正"""
    lines = content.split('\n')
    fixed_lines = []
    in_fixture = False
    after_manager_line = False
    
    for i, line in enumerate(lines):
        # フィクスチャの開始
        if 'def tables_manager():' in line:
            in_fixture = True
            fixed_lines.append(line)
            continue
        
        # フィクスチャの終了（yield の後の行から）
        if in_fixture and line.strip().startswith('yield manager'):
            fixed_lines.append(line)
            in_fixture = False
            continue
        
        # フィクスチャ内の処理
        if in_fixture:
            # manager = TablesManager() の次の行からインデントが必要
            if 'manager = TablesManager()' in line:
                fixed_lines.append(line)
                after_manager_line = True
                continue
            
            # インデントが必要な行
            if after_manager_line and line.strip():
                # すでに4スペースでインデントされていなければ追加
                if not line.startswith('    ') and not line.startswith('yield'):
                    line = '    ' + line.lstrip()
            
            fixed_lines.append(line)
        else:
            after_manager_line = False
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def main():
    """メイン処理"""
    count = 0
    for file_path in sorted(test_dir.glob('test_*.py')):
        if file_path.name == 'test_add_column.py':
            continue
        
        content = file_path.read_text(encoding='utf-8')
        fixed = fix_fixture_indent(content)
        
        if fixed != content:
            file_path.write_text(fixed, encoding='utf-8')
            count += 1
            print(f"修正: {file_path.name}")
    
    print(f"\n合計: {count}ファイル")


if __name__ == '__main__':
    main()
