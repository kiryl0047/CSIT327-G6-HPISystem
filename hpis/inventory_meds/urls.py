from django.urls import path
from . import views

app_name = "inventory_meds"

urlpatterns = [
    # Dashboard
    path("", views.inventory_dashboard, name="dashboard"),
    
    # Medicine CRUD
    path("add/", views.add_medicine, name="add_medicine"),
    path("medicine/<int:medicine_id>/", views.view_medicine, name="view_medicine"),
    path("medicine/<int:medicine_id>/edit/", views.edit_medicine, name="edit_medicine"),
    path("medicine/<int:medicine_id>/archive/", views.archive_medicine, name="archive_medicine"),
    
    # Stock Management
    path("medicine/<int:medicine_id>/adjust-stock/", views.adjust_stock, name="adjust_stock"),
    
    # Dispensing
    path("dispense/", views.dispense_medicine, name="dispense_medicine"),
    path("medicine/<int:medicine_id>/dispense/", views.dispense_medicine, name="dispense_medicine_specific"),
    
    # Reports
    path("reports/", views.reports_dashboard, name="reports_dashboard"),
    path("reports/inventory-summary/", views.inventory_summary_report, name="inventory_summary"),
    path("reports/low-stock/", views.low_stock_report, name="low_stock_report"),
    path("reports/expiring/", views.expiring_items_report, name="expiring_report"),
    path("reports/expired/", views.expired_items_report, name="expired_report"),
    path("reports/stock-movement/", views.stock_movement_report, name="stock_movement_report"),
    path("reports/dispensing/", views.dispensing_summary_report, name="dispensing_report"),
    
    # Export
    path("export/csv/", views.export_inventory_csv, name="export_csv"),
    
    # Audit Logs
    path("audit-logs/", views.audit_log_view, name="audit_logs"),
]
