"""テストファイルの全構文エラーを修正"""
import re
from pathlib import Path

test_dir = Path('tests')


def fix_test_file(content):
    """構文エラーを修正"""
    # 余分な括弧を削除
    content = re.sub(r'status\.HTTP_(\w+)\)', r'status.HTTP_\1', content)
    content = re.sub(r"(\[None(?:, None)*\])\)", r'\1', content)
    
    # カンマ演算子を==に
    content = re.sub(r"assert response_data\['(\w+)'\], '(\w+)'\)", r"assert response_data['\1'] == '\2'", content)
    
    # 不完全な括弧
    content = re.sub(r'tables_manager\.get_table_name_list\(\s*\n', 'tables_manager.get_table_name_list()\n', content)
    
    # assertIn の修正
    content = re.sub(r"assert '(\w+)', ", r"assert '\1' in ", content)
    
    # タプルの括弧
    content = re.sub(r'== \((\d+, \d+)\)', r'== (\1)', content)
    
    # 複数行にわたるassertIn の修正
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # assert response_data['message'], の修正
        if "assert response_data['message']," in line:
            # 次の行を取得
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('"') or next_line.startswith("'"):
                    # マージ
                    indent = len(line) - len(line.lstrip())
                    message = next_line.strip().rstrip(')')
                    line = ' ' * indent + f"assert {message} in response_data['message']"
                    i += 1  # 次の行をスキップ
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def main():
    """メイン処理"""
    count = 0
    for file_path in sorted(test_dir.glob('test_*.py')):
        if file_path.name == 'test_add_column.py':
            continue
        
        content = file_path.read_text(encoding='utf-8')
        fixed = fix_test_file(content)
        file_path.write_text(fixed, encoding='utf-8')
        count += 1
        print(f"修正: {file_path.name}")
    
    print(f"\n合計: {count}ファイル")


if __name__ == '__main__':
    main()
