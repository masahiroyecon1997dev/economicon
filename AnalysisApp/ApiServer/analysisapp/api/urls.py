from django.urls import path
from . import views
from .apis import read_csv
from .apis import write_csv
from .apis import import_csv
from .apis import output_csv
from .apis import fetch_data_to_json
from .apis import get_table_name_list
from .apis import get_column_name_list
from .apis import generate_simulation_data

urlpatterns = [
    path('', views.index, name='index'),
    path('read_csv', read_csv.ReadCsv.as_view()),
    path('write_csv', write_csv.WriteCsv.as_view()),
    path('import_csv', import_csv.ImportCsv.as_view()),
    path('output_csv', output_csv.OutputCsv.as_view()),
    path('fetch_data_to_json', fetch_data_to_json.FetchDataToJson.as_view()),
    path('get_table_name_list', get_table_name_list.GetTableNameList
         .as_view()),
    path('get_column_name_list', get_column_name_list.GetColumnNameList
         .as_view()),
    path('generate_simulation_data', generate_simulation_data.
         GenerateSimulationData.as_view()),
]
