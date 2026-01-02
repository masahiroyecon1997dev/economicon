"""変換後のテストファイルを修正"""
import re
from pathlib import Path

test_dir = Path('tests')
exclude_files = ['test_add_column.py', 'conftest.py', '__init__.py']


def fix_converted_test(content):
    """変換後のテストファイルを修正"""
    lines = content.split('\n')
    fixed_lines = []
    in_function = False
    
    for i, line in enumerate(lines):
        # 関数定義の検出
        if line.startswith('def test_'):
            in_function = True
            fixed_lines.append(line)
            continue
        
        # 空行と関数外はそのまま
        if not in_function or not line.strip():
            fixed_lines.append(line)
            if line and not line.startswith(' ') and in_function:
                in_function = False
            continue
        
        # インデント修正（関数内は4スペース）
        if line.startswith('        '):  # 8スペース → 4スペース
            line = line[4:]
        
        # 余分な括弧を削除
        line = re.sub(r'(\) *)\)$', r'\1', line)
        
        # self.assertEqual の残りを修正
        if 'self.assertEqual(' in line:
            # self.assertEqual(a, b) → assert a == b
            match = re.search(r'self\.assertEqual\((.*?), (.*?)\)', line)
            if match:
                left = match.group(1)
                right = match.group(2)
                indent = len(line) - len(line.lstrip())
                line = ' ' * indent + f'assert {left} == {right}'
        
        # assertIn/assertNotIn の修正
        if 'assert ' in line and ',' in line and ' in ' not in line and ' not in ' not in line:
            # assert 'item', collection) → assert 'item' in collection
            match = re.search(r"assert (['\"]?\w+['\"]?), (.+)$", line)
            if match:
                item = match.group(1)
                collection = match.group(2).rstrip(')')
                indent = len(line) - len(line.lstrip())
                line = ' ' * indent + f'assert {item} in {collection}'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def main():
    """メイン処理"""
    print("テストファイルの修正を開始...")
    fixed_count = 0
    
    for file_path in sorted(test_dir.glob('test_*.py')):
        if file_path.name in exclude_files:
            continue
        
        print(f"修正中: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixed = fix_converted_test(content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed)
            
            fixed_count += 1
            print(f"  ✓ 修正完了")
        
        except Exception as e:
            print(f"  ✗ エラー: {e}")
    
    print(f"\n修正完了: {fixed_count}ファイル")


if __name__ == '__main__':
    main()
