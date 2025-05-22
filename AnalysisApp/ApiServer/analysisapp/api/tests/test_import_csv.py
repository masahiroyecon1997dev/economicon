from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
import polars as pl

from ..apis.import_csv import ImportCsv
from ..apis.tables import tables


class ApiImportCsvTests(APITestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.test_data = None

    def setUp(self):
        self.test_data = pl.read_csv('/AnalysisApp/SampleData/TestData1.csv',
                                     encoding='utf8')

    def test_import_csv_api_1(self):
        test_file = File(open('/AnalysisApp/SampleData/TestData1.csv', 'rb'))
        uploaded_file = SimpleUploadedFile('TestData1.csv', test_file.read(),
                                           content_type='multipart/form-data')
        factory = APIRequestFactory()
        request = factory.post('/import-csv', {'file': uploaded_file},
                               'multipart')
        view = ImportCsv.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual(0, response.data['code'])
        self.assertEqual('TestData1', response.data['result']['tableName'])
        data = tables['TestData1']
        self.assertEqual(True, self.test_data.equals(data))

    def test_import_csv_api_2(self):
        factory = APIRequestFactory()
        request = factory.post('/import-csv')
        view = ImportCsv.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # レスポンスデータの検証
        self.assertEqual(-9999, response.data['code'])
        self.assertEqual('', response.data['result']['tableName'])
