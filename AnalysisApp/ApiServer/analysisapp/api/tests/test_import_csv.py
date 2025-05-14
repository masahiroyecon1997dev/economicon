from rest_framework.test import APITestCase
from rest_framework import status


class APIViewTests(APITestCase):
    @classmethod
    def test_sample_get_api(self):
        response = self.client.post('/import_csv')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['username'], 'john_doe')
