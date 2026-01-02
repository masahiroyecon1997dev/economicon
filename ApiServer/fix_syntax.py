"""テストファイルの構文エラーを修正"""
import re
from pathlib import Path

test_dir = Path('tests')


def fix_all_issues(content):
    """すべての構文エラーを修正"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        original = line
        
        # 1. 余分な閉じ括弧を削除
        if 'assert ' in line:
            # assert response.status_code == status.HTTP_200_OK) → HTTP_200_OK
            line = re.sub(r'(status\.HTTP_\w+)\)', r'\1', line)
            # assert response_data['code'], 'OK') → 'OK'
            if \"'], '\" in line and line.count(\"'\") >= 3:
                line = re.sub(r\"(response_data\['\\w+'\]), ('\\w+'\)), r\"\1 == \2\", line)
            # [None, None, None]) → [None, None, None]
            line = re.sub(r'(\[None, None(, None)*\])\)', r'\1', line)
        
        # 2. カンマ演算子を == に修正
        if 'assert response_data[' in line and \"'], '\" in line and '==' not in line:
            match = re.search(r\"(response_data\['\\w+'\]), ('\\w+')\", line)
            if match:
                indent = len(line) - len(line.lstrip())
                line = ' ' * indent + f'assert {match.group(1)} == {match.group(2)}'
        
        # 3. 不完全な括弧を修正
        if line.rstrip().endswith('('):
            # 次の行を見て判断
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith(')'):
                    line = line.rstrip()[:-1]  # 括弧を削除
        
        # 4. get_table_name_list( の修正
        if 'tables_manager.get_table_name_list(' in line and not line.rstrip().endswith(')'):
            line = line.rstrip() + ')'
        
        # 5. タプルの括弧修正
        # (3, 2) → (3, 2)
        line = re.sub(r'== \((\d+, \d+)\)', r'== (\1)', line)
        
        # 6. assert文のカンマを==に
        if 'assert response_data[' in line and ',' in line and ' in ' not in line:
            # カンマで分割されている場合
            parts = line.split(',')
            if len(parts) == 2 and '==' not in line:
                indent = len(line) - len(line.lstrip())
                left = parts[0].replace('assert ', '').strip()
                right = parts[1].strip().rstrip(')')
                line = ' ' * indent + f'assert {left} == {right}'
        
        # 7. assertIn の修正
        if \"assert '\" in line and \", \" in line and ' in ' not in line and ' not in ' not in line and '==' not in line:
            match = re.search(r"assert '(\w+)', (.+)$", line)
            if match:
                item = f\"'{match.group(1)}'\"
                collection = match.group(2).strip().rstrip(')')
                indent = len(line) - len(line.lstrip())
                line = ' ' * indent + f'assert {item} in {collection}'
        
        # 8. フィクスチャ内のインデント修正
        if line.strip() and line.startswith('@pytest.fixture'):
            fixed_lines.append(line)
            continue
        
        # yield の前の行をチェック
        if i > 0 and 'yield manager' in lines[i]:
            # yield の前の行がインデントされているべき
            prev_line = fixed_lines[-1] if fixed_lines else ''
            if prev_line.strip() and not prev_line.startswith('    '):
                if 'manager.' in prev_line or 'df = ' in prev_line:
                    fixed_lines[-1] = '    ' + prev_line.lstrip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def main():
    """メイン処理"""
    print("構文エラーを修正中...")
    
    for file_path in sorted(test_dir.glob('test_*.py')):
        if file_path.name == 'test_add_column.py':
            continue
        
        print(f"修正: {file_path.name}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            fixed = fix_all_issues(content)
            file_path.write_text(fixed, encoding='utf-8')
            print(f"  ✓ 完了")
        except Exception as e:
            print(f"  ✗ エラー: {e}")
    
    print("\n修正完了")


if __name__ == '__main__':
    main()
