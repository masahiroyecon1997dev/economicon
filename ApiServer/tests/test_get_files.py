import pytest
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from analysisapp.api.services.data.tables_manager import TablesManager


@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def tables_manager():
    """TablesManagerのフィクスチャ"""
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
    yield manager
    # テスト後のクリーンアップ
    manager.clear_tables()



def test_get_list_files_success(client, tables_manager):
    """
    正常にファイル一覧を取得できる
    """
    response = client.get(
        '/api/get-files'
        f'?directoryPath={self.test_dir}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['directoryPath'] == self.test_dir
    assert 'files' in result
    files = result['files']
    assert len(files) == 3
    # アイテムが名前順でソートされているか確認
    item_names = [item['name'] for item in files]
    assert item_names == ['subdir', 'test1.txt', 'test2.txt']
    # 各アイテムの情報を確認
    for item in files:
        assert 'name' in item
        assert 'isFile' in item
        assert 'size' in item
        assert 'modifiedTime' in item
        # ファイルとディレクトリの判定確認
        if item['name'] == 'subdir':
            assert not item['isFile'])
            assert item['size'] == 0
        elif item['name'].endswith('.txt'):
            assert item['isFile'])
            self.assertGreater(item['size'], 0)
        # 更新日時が適切な形式か確認
        try:
            datetime.fromisoformat(item['modifiedTime'])
        except ValueError:
            self.fail(f"Invalid datetime format: {item['modifiedTime']}")


def test_get_list_files_empty_directory(client, tables_manager):
    """
    空のディレクトリの場合
    """
    empty_dir = tempfile.mkdtemp()
    try:
        response = client.get(
            '/api/get-files'
            f'?directoryPath={empty_dir}',
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert response_data['code'] == 'OK'
        result = response_data['result']
        assert result['directoryPath'] == empty_dir
        assert len(result['files']) == 0
    finally:
        shutil.rmtree(empty_dir)


def test_get_list_files_invalid_directory(client, tables_manager):
    """
    存在しないディレクトリを指定した場合のテスト
    """
    response = client.get(
        '/api/get-files'
        '?directoryPath=/non/existent/directory',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Directory does not exist", response_data['message'])


def test_get_list_files_missing_directory_path(client, tables_manager):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    response = client.get(
        '/api/get-files'
        '?directoryPath=',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "directoryPath is required", response_data['message'])


def test_get_list_files_file_instead_of_directory(client, tables_manager):
    """
    ディレクトリではなくファイルのパスを指定した場合のテスト
    """
    response = client.get(
        '/api/get-files'
        f'?directoryPath={self.test_file1}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Path is not a directory", response_data['message'])


def test_get_list_files_file_sizes(client, tables_manager):
    """
    ファイルサイズが正しく取得できることを確認
    """
    response = client.get(
        '/api/get-files'
        f'?directoryPath={self.test_dir}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    files = response_data['result']['files']
    # test1.txtのサイズ確認
    test1_item = next(
        item for item in files if item['name'] == 'test1.txt'
    )
    assert test1_item['size'] == len('test content 1'
    # test2.txtのサイズ確認
    test2_item = next(
        item for item in files if item['name'] == 'test2.txt'
    )
    self.assertEqual(test2_item['size'],
                     len('test content 2 with more data')
    # サブディレクトリのサイズ確認
    subdir_item = next(
        item for item in files if item['name'] == 'subdir'
    )
    assert subdir_item['size'] == 0
