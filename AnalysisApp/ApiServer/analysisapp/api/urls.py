from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('read_csv', views.ReadCsv.as_view()),
    path('write_csv', views.WriteCsv.as_view()),
    path('import_csv', views.ImportCsv.as_view()),
    path('output_csv', views.OutputCsv.as_view()),
    path('fetch_data_to_json', views.FetchDataToJson.as_view()),
    path('get_table_name_list', views.GetTableNameList.as_view()),
    path('get_column_name_list', views.GetColumnNameList.as_view()),
    path('generate_simulation_data', views.GenerateSimulationData.as_view()),
]
