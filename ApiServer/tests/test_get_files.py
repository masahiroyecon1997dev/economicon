import pytest
from fastapi.testclient import TestClient
from fastapi import status
import os
import tempfile
import shutil
from datetime import datetime

from main import app
from analysisapp.services.data.tables_manager import TablesManager

# テスト用の一時ディレクトリを作成
test_dir = ''

@pytest.fixture
def client():
    """TestClientのフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def prepared_data():
    """TablesManagerのフィクスチャ"""
    tables_manager = TablesManager()
    # テスト用の一時ディレクトリを作成
    test_dir = tempfile.mkdtemp()
    # テスト用のファイルとディレクトリを作成
    test_file1 = os.path.join(test_dir, 'test1.txt')
    test_file2 = os.path.join(test_dir, 'test2.txt')
    test_subdir = os.path.join(test_dir, 'subdir')
    # ファイルを作成
    with open(test_file1, 'w') as f:
        f.write('test content 1')
    with open(test_file2, 'w') as f:
        f.write('test content 2 with more data')
    # サブディレクトリを作成
    os.makedirs(test_subdir)
    yield tables_manager, test_dir, test_file1, test_file2, test_subdir
    # テスト後にクリーンアップ
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    # テスト後のクリーンアップ
    tables_manager.clear_tables()



def test_get_list_files_success(client, prepared_data):
    """
    正常にファイル一覧を取得できる
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
    response = client.get(
        '/api/get-files'
        f'?directoryPath={test_dir}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data['code'] == 'OK'
    result = response_data['result']
    assert result['directoryPath'] == test_dir
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
            assert not item['isFile']
            assert item['size'] == 0
        elif item['name'].endswith('.txt'):
            assert item['isFile']
            assert item['size'] > 0
        # 更新日時が適切な形式か確認
        try:
            datetime.fromisoformat(item['modifiedTime'])
        except ValueError:
            assert False, f"Invalid datetime format: {item['modifiedTime']}"


def test_get_list_files_empty_directory(client, prepared_data):
    """
    空のディレクトリの場合
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
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


def test_get_list_files_invalid_directory(client, prepared_data):
    """
    存在しないディレクトリを指定した場合のテスト
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
    response = client.get(
        '/api/get-files'
        '?directoryPath=/non/existent/directory',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Directory does not exist" == response_data['message']


def test_get_list_files_missing_directory_path(client, prepared_data):
    """
    directoryPathパラメータが未指定の場合のテスト
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
    response = client.get(
        '/api/get-files'
        '?directoryPath=',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "directoryPath is required" == response_data['message']


def test_get_list_files_file_instead_of_directory(client, prepared_data):
    """
    ディレクトリではなくファイルのパスを指定した場合のテスト
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
    response = client.get(
        '/api/get-files'
        f'?directoryPath={test_file1}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response_data['code'] == 'NG'
    assert "Path is not a directory" == response_data['message']


def test_get_list_files_file_sizes(client, prepared_data):
    """
    ファイルサイズが正しく取得できることを確認
    """
    tables_manager, test_dir, test_file1, test_file2, test_subdir = prepared_data
    response = client.get(
        '/api/get-files'
        f'?directoryPath={test_dir}',
    )
    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    files = response_data['result']['files']
    # test1.txtのサイズ確認
    test1_item = next(
        item for item in files if item['name'] == 'test1.txt'
    )
    assert test1_item['size'] == len('test content 1')
    # test2.txtのサイズ確認
    test2_item = next(
        item for item in files if item['name'] == 'test2.txt'
    )
    assert test2_item['size'] == len('test content 2 with more data')
    # サブディレクトリのサイズ確認
    subdir_item = next(
        item for item in files if item['name'] == 'subdir'
    )
    assert subdir_item['size'] == 0
