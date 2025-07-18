from rest_framework.test import APITestCase
from rest_framework import status
import json
from ..apis.data.tables_manager import TablesManager
import polars as pl


class TestApiCreateJoinTable(APITestCase):
    def setUp(self):
        self.tables_manager = TablesManager()
        self.tables_manager.clear_tables()
        # テーブルをクリア
        self.tables_manager.clear_tables()
        # 左テーブル
        left_df = pl.DataFrame({
            'id': [1, 2, 3, 4],
            'val_left': ['A', 'B', 'C', 'D']
        })
        self.tables_manager.store_table('LeftTable', left_df)

        # 右テーブル
        right_df = pl.DataFrame({
            'id': [3, 4, 5, 6],
            'val_right': ['X', 'Y', 'Z', 'W']
        })
        self.tables_manager.store_table('RightTable', right_df)

    def test_inner_join(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('JoinTable').table
        self.assertEqual(df.shape, (2, 3))
        self.assertListEqual(df['id'].to_list(), [3, 4])
        self.assertListEqual(df['val_left'].to_list(), ['C', 'D'])
        self.assertListEqual(df['val_right'].to_list(), ['X', 'Y'])

    def test_left_join(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'left'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('JoinTable').table
        self.assertEqual(df.shape, (4, 3))
        self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4])
        self.assertListEqual(df['val_left'].to_list(), ['A', 'B', 'C', 'D'])
        self.assertListEqual(df['val_right'].to_list(), [None, None, 'X', 'Y'])

    def test_right_join(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'right'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('JoinTable').table
        self.assertEqual(df.shape, (4, 3))
        self.assertListEqual(df['id'].to_list(), [3, 4, 5, 6])
        self.assertListEqual(df['val_left'].to_list(), ['C', 'D', None, None])
        self.assertListEqual(df['val_right'].to_list(), ['X', 'Y', 'Z', 'W'])

    def test_outer_join(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'outer'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data['code'], 'OK')
        df = self.tables_manager.get_table('JoinTable').table
        self.assertEqual(df.shape, (6, 3))
        self.assertListEqual(df['id'].to_list(), [1, 2, 3, 4, 5, 6])
        self.assertListEqual(df['val_left'].to_list(), ['A', 'B', 'C', 'D',
                                                        None, None])
        self.assertListEqual(df['val_right'].to_list(), [None, None, 'X', 'Y',
                                                         'Z', 'W'])

    def test_join_table_name_empty(self):
        payload = {
            'joinTableName': '',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'], "joinTableName is required.")

    def test_left_table_not_found(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'NotExist',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "leftTableName 'NotExist' does not exist.")

    def test_right_table_not_found(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'NotExist',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "rightTableName 'NotExist' does not exist.")

    def test_left_key_column_not_found(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['not_exist_col'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "leftKeyColumnNames 'not_exist_col' does not exist.")

    def test_right_key_column_not_found(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['not_exist_col'],
            'joinType': 'inner'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "rightKeyColumnNames 'not_exist_col' does not exist.")

    def test_invalid_join_type(self):
        payload = {
            'joinTableName': 'JoinTable',
            'leftTableName': 'LeftTable',
            'rightTableName': 'RightTable',
            'leftKeyColumnNames': ['id'],
            'rightKeyColumnNames': ['id'],
            'joinType': 'invalid_type'
        }
        response = self.client.post(
            '/api/create-join-table',
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_data['code'], 'NG')
        self.assertIn(response_data['message'],
                      "joinType 'invalid_type' is not a valid value.")
