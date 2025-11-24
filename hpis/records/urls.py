from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_patient_record, name='create_patient_record'),
    path('<int:pk>/', views.patient_record_detail, name='patient_record_detail'),
    path('<int:pk>/edit/', views.update_patient_record, name='update_patient_record'),
    path('', views.records_list, name='records_list'),
    path('<int:pk>/log/', views.add_visit_log, name='add_visit_log'),
    path('<int:pk>/pdf/', views.download_patient_pdf, name='download_patient_pdf'),
]