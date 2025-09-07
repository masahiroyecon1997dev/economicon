from rest_framework.test import APITestCase
from rest_framework import status
import json
import tempfile
import os
import shutil
from datetime import datetime


class TestApiGetListFiles(APITestCase):
    def setUp(self):
        # テスト用の一時ディレクトリを作成
        self.test_dir = tempfile.mkdtemp()

        # テスト用のファイルとディレクトリを作成
        self.test_file1 = os.path.join(self.test_dir, 'test1.txt')
        self.test_file2 = os.path.join(self.test_dir, 'test2.txt')
        self.test_subdir = os.path.join(self.test_dir, 'subdir')

        # ファイルを作成
        with open(self.test_file1, 'w') as f:
            f.write('test content 1')
        with open(self.test_file2, 'w') as f:
            f.write('test content 2 with more data')

        # サブディレクトリを作成
        os.makedirs(self.test_subdir)

    def tearDown(self):
        # テスト後にクリーンアップ
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_list_files_success(self):
        """
        正常にファイル一覧を取得できる
        """
        payload = {
            'directoryPath': self.test_dir
        }
        response = self.client.post(
            '/api/get-list-files',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')

        result = response_data['result']
        self.assertEqual(result['directoryPath'], self.test_dir)
        self.assertIn('items', result)

        items = result['items']
        self.assertEqual(len(items), 3)  # 2 files + 1 directory

        # アイテムが名前順でソートされているか確認
        item_names = [item['name'] for item in items]
        self.assertEqual(item_names, ['subdir', 'test1.txt', 'test2.txt'])

        # 各アイテムの情報を確認
        for item in items:
            self.assertIn('name', item)
            self.assertIn('isFile', item)
            self.assertIn('size', item)
            self.assertIn('modifiedTime', item)

            # ファイルとディレクトリの判定確認
            if item['name'] == 'subdir':
                self.assertFalse(item['isFile'])
                self.assertEqual(item['size'], 0)
            elif item['name'].endswith('.txt'):
                self.assertTrue(item['isFile'])
                self.assertGreater(item['size'], 0)

            # 更新日時が適切な形式か確認
            try:
                datetime.fromisoformat(item['modifiedTime'])
            except ValueError:
                self.fail(f"Invalid datetime format: {item['modifiedTime']}")

    def test_get_list_files_empty_directory(self):
        """
        空のディレクトリの場合
        """
        empty_dir = tempfile.mkdtemp()
        try:
            payload = {
                'directoryPath': empty_dir
            }
            response = self.client.post(
                '/api/get-list-files',
                data=json.dumps(payload),
                content_type='application/json'
            )

            response_data = response.json()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data['code'], 'OK')

            result = response_data['result']
            self.assertEqual(result['directoryPath'], empty_dir)
            self.assertEqual(len(result['items']), 0)
        finally:
            shutil.rmtree(empty_dir)

    def test_get_list_files_invalid_directory(self):
        """
        存在しないディレクトリを指定した場合のテスト
        """
        payload = {
            'directoryPath': '/non/existent/directory'
        }
        response = self.client.post(
            '/api/get-list-files',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Directory does not exist", response_data['message'])

    def test_get_list_files_missing_directory_path(self):
        """
        directoryPathパラメータが未指定の場合のテスト
        """
        payload = {}
        response = self.client.post(
            '/api/get-list-files',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("directoryPath is required", response_data['message'])

    def test_get_list_files_file_instead_of_directory(self):
        """
        ディレクトリではなくファイルのパスを指定した場合のテスト
        """
        payload = {
            'directoryPath': self.test_file1
        }
        response = self.client.post(
            '/api/get-list-files',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn("Path is not a directory", response_data['message'])

    def test_get_list_files_file_sizes(self):
        """
        ファイルサイズが正しく取得できることを確認
        """
        payload = {
            'directoryPath': self.test_dir
        }
        response = self.client.post(
            '/api/get-list-files',
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        items = response_data['result']['items']

        # test1.txtのサイズ確認
        test1_item = next(
            item for item in items if item['name'] == 'test1.txt'
        )
        self.assertEqual(test1_item['size'], len('test content 1'))

        # test2.txtのサイズ確認
        test2_item = next(
            item for item in items if item['name'] == 'test2.txt'
        )
        self.assertEqual(test2_item['size'],
                         len('test content 2 with more data'))

        # サブディレクトリのサイズ確認
        subdir_item = next(
            item for item in items if item['name'] == 'subdir'
        )
        self.assertEqual(subdir_item['size'], 0)
