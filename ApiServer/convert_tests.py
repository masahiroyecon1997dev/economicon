"""テストファイルをDjango形式からpytest形式に一括変換"""
import re
from pathlib import Path

test_dir = Path('tests')
exclude_files = ['test_add_column.py', 'conftest.py', '__init__.py']


def convert_django_to_pytest(content):
    """Django TestCaseをpytest形式に変換"""
    # 基本的なインポート置換
    content = content.replace('from rest_framework.test import APITestCase\n', '')
    content = content.replace('from rest_framework import status\n', '')
    content = content.replace('import json\n', '')
    content = content.replace('from ..apis.data.tables_manager import TablesManager',
                              'from analysisapp.api.services.data.tables_manager import TablesManager')
    
    # クラス定義を確認
    if 'class TestApi' not in content or 'APITestCase' not in content:
        return None
    
    # インポートセクションを作成
    imports = [
        'import pytest',
        'from fastapi.testclient import TestClient',
        'from fastapi import status'
    ]
    
    if 'import polars' in content:
        imports.append('import polars as pl')
    
    imports.extend([
        '',
        'from main import app',
        'from analysisapp.api.services.data.tables_manager import TablesManager'
    ])
    
    # フィクスチャを作成
    fixtures = [
        '',
        '',
        '@pytest.fixture',
        'def client():',
        '    """TestClientのフィクスチャ"""',
        '    return TestClient(app)',
        '',
        ''
    ]
    
    # setUpメソッドをフィクスチャに変換
    lines = content.split('\n')
    setup_fixture = []
    test_functions = []
    
    in_class = False
    in_setup = False
    in_test = False
    current_test_lines = []
    current_test_name = ''
    
    for i, line in enumerate(lines):
        # クラス定義をスキップ
        if 'class TestApi' in line:
            in_class = True
            continue
        
        if not in_class:
            continue
        
        # setUpメソッドを検出
        if '    def setUp(self):' in line:
            in_setup = True
            setup_fixture = [
                '@pytest.fixture',
                'def tables_manager():',
                '    """TablesManagerのフィクスチャ"""'
            ]
            continue
        
        # setUpの中身を処理
        if in_setup:
            if line.strip() and line.startswith('    def test_'):
                # setUpが終わった
                in_setup = False
                setup_fixture.extend([
                    '    yield manager',
                    '    # テスト後のクリーンアップ',
                    '    manager.clear_tables()',
                    ''
                ])
            elif 'self.tables_manager = TablesManager()' in line:
                setup_fixture.append('    manager = TablesManager()')
            elif 'self.tables_manager.' in line:
                setup_fixture.append(line.replace('self.tables_manager.', 'manager.'))
            elif line.strip():
                setup_fixture.append(line)
        
        # テストメソッドを検出
        if '    def test_' in line and not in_setup:
            # 前のテストを保存
            if current_test_lines:
                test_functions.append('\n'.join(current_test_lines))
                current_test_lines = []
            
            in_test = True
            # メソッド名を抽出
            match = re.search(r'def (test_\w+)\(self\):', line)
            if match:
                current_test_name = match.group(1)
                current_test_lines.append(f'def {current_test_name}(client, tables_manager):')
            continue
        
        # テストメソッドの中身を処理
        if in_test:
            if line.strip() and (line.startswith('    def ') or line.startswith('class ')):
                # 次のメソッドまたはクラスの開始
                in_test = False
                if current_test_lines:
                    test_functions.append('\n'.join(current_test_lines))
                    current_test_lines = []
            else:
                # テストコードを変換
                converted = line
                
                # self.client → client
                converted = converted.replace('self.client.post(', 'client.post(')
                converted = converted.replace('self.client.get(', 'client.get(')
                
                # self.tables_manager → tables_manager
                converted = converted.replace('self.tables_manager.', 'tables_manager.')
                
                # JSONリクエストの形式を変更
                converted = converted.replace('data=json.dumps(payload),', 'json=payload,')
                converted = converted.replace("content_type='application/json'", '')
                converted = converted.replace("content_type='application/json',", '')
                
                # アサーションを変換
                converted = converted.replace('self.assertEqual(response.status_code, ', 'assert response.status_code == ')
                converted = converted.replace('self.assertEqual(response_data[', 'assert response_data[')
                converted = converted.replace('self.assertIn(', 'assert ')
                converted = converted.replace('self.assertNotIn(', 'assert ')
                converted = converted.replace('self.assertTrue(', 'assert ')
                converted = converted.replace('self.assertFalse(', 'assert not ')
                
                # assertEqual の残りを修正
                if ', status.HTTP_' in converted and 'assert response.status_code' in converted:
                    converted = re.sub(r'\)', '', converted)
                
                if "assert response_data\\['" in converted:
                    converted = re.sub(r"assert response_data\['(\w+)'\], (.*?)\)", r"assert response_data['\1'] == \2", converted)
                
                # assertIn/assertNotIn の修正
                if 'assert ' in converted and ',' in converted and ')' in converted:
                    # assert 'item', collection) → assert 'item' in collection
                    match = re.search(r"assert (['\"]?\w+['\"]?), (.+?)\)", converted)
                    if match and 'assert not ' not in converted:
                        item = match.group(1)
                        collection = match.group(2)
                        indent = len(converted) - len(converted.lstrip())
                        if 'Not' in line:  # 元が assertNotIn
                            converted = ' ' * indent + f"assert {item} not in {collection}"
                        else:
                            converted = ' ' * indent + f"assert {item} in {collection}"
                
                if converted.strip():
                    current_test_lines.append(converted)
    
    # 最後のテストを保存
    if current_test_lines:
        test_functions.append('\n'.join(current_test_lines))
    
    # ファイル全体を組み立て
    result = []
    result.extend(imports)
    result.extend(fixtures)
    
    if setup_fixture and len(setup_fixture) > 3:
        result.extend(setup_fixture)
        result.append('')
    
    for func in test_functions:
        result.append('')
        result.append(func)
        result.append('')
    
    return '\n'.join(result)


def main():
    """メイン処理"""
    print("テストファイルの変換を開始...")
    converted_count = 0
    error_count = 0
    
    for file_path in sorted(test_dir.glob('test_*.py')):
        if file_path.name in exclude_files:
            print(f"スキップ: {file_path.name}")
            continue
        
        print(f"変換中: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            converted = convert_django_to_pytest(content)
            
            if converted:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(converted)
                converted_count += 1
                print(f"  ✓ 変換完了")
            else:
                print(f"  - 変換不要またはスキップ")
        
        except Exception as e:
            print(f"  ✗ エラー: {e}")
            error_count += 1
    
    print(f"\n変換完了: {converted_count}ファイル")
    if error_count > 0:
        print(f"エラー: {error_count}ファイル")


if __name__ == '__main__':
    main()
