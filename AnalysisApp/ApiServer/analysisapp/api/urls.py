from django.urls import path
from . import views
from .apis import (read_csv,
                   write_csv,
                   import_csv_by_file,
                   import_tsv_by_file,
                   import_excel_by_file,
                   output_csv,
                   fetch_data_to_json,
                   get_table_name_list,
                   get_column_name_list,
                   generate_simulation_data,
                   linear_regression,
                   create_table,
                   add_column)

urlpatterns = [
    path('', views.index, name='index'),
    path('read-csv', read_csv.ReadCsv.as_view()),
    path('write-csv', write_csv.WriteCsv.as_view()),
    path('import-csv-by-file', import_csv_by_file.ImportCsvByFile.as_view()),
    path('import-tsv-by-file', import_tsv_by_file.ImportTsvByFile.as_view()),
    path('import-excel-by-file', import_excel_by_file.ImportExcelByFile
         .as_view()),
    path('add-column', add_column.AddColumn.as_view()),
    path('create-table', create_table.CreateTable.as_view()),
    path('output-csv', output_csv.OutputCsv.as_view()),
    path('fetch-data_to_json', fetch_data_to_json.FetchDataToJson.as_view()),
    path('get-table-name-list', get_table_name_list.GetTableNameList
         .as_view()),
    path('get-column-name-list', get_column_name_list.GetColumnNameList
         .as_view()),
    path('generate-simulation-data', generate_simulation_data.
         GenerateSimulationData.as_view()),
    path('linear-regression', linear_regression.
         LinearRegression.as_view()),

]
