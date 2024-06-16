from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('read_csv', views.ReadCsv.as_view()),
    path('write_csv', views.WriteCsv.as_view()),
]
