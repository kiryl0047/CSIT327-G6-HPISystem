from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    # Placeholder endpoints; to be implemented per spec
    path("", views.inventory_dashboard, name="dashboard"),
]
