from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("accounts/login/", views.ImacidLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),

    path("", views.dashboard_view, name="dashboard"),

    # Commandes
    path("commandes/", views.order_list, name="order_list"),
    path("commandes/ajouter/", views.order_form_view, name="order_create"),
    path("commandes/<int:pk>/modifier/", views.order_form_view, name="order_update"),
    path("commandes/<int:pk>/supprimer/", views.order_delete, name="order_delete"),
    path("commandes/<int:pk>/", views.order_detail, name="order_detail"),

    # Fournisseurs
    path("fournisseurs/", views.supplier_list, name="supplier_list"),
    path("fournisseurs/ajouter/", views.supplier_form_view, name="supplier_create"),
    path("fournisseurs/<int:pk>/modifier/", views.supplier_form_view, name="supplier_update"),
    path("fournisseurs/<int:pk>/supprimer/", views.supplier_delete, name="supplier_delete"),
    path("fournisseurs/<int:pk>/", views.supplier_detail, name="supplier_detail"),

    # Transport
    path("transport/", views.transport_list, name="transport_list"),
    path("transport/ajouter/", views.transport_form_view, name="transport_create"),
    path("transport/<int:pk>/modifier/", views.transport_form_view, name="transport_update"),
    path("transport/<int:pk>/supprimer/", views.transport_delete, name="transport_delete"),

    # Transit
    path("transit/", views.transit_list, name="transit_list"),
    path("transit/ajouter/", views.transit_form_view, name="transit_create"),
    path("transit/<int:pk>/modifier/", views.transit_form_view, name="transit_update"),
    path("transit/<int:pk>/supprimer/", views.transit_delete, name="transit_delete"),

    # Litiges
    path("litiges/", views.dispute_list, name="dispute_list"),
    path("litiges/ajouter/", views.dispute_form_view, name="dispute_create"),
    path("litiges/<int:pk>/modifier/", views.dispute_form_view, name="dispute_update"),
    path("litiges/<int:pk>/supprimer/", views.dispute_delete, name="dispute_delete"),

    # KPI & analyses
    path("kpi/", views.kpi_view, name="kpi"),
    path("analyse/surcouts/", views.analysis_overrun_view, name="analysis_overrun"),
    path("analyse/retards/", views.analysis_delay_view, name="analysis_delay"),
    path("fournisseurs-classement/", views.supplier_ranking_view, name="supplier_ranking"),
    path("recommandations/", views.recommendations_view, name="recommendations"),

    # Plan d'action
    path("plan-action/", views.action_plan_list, name="action_plan_list"),
    path("plan-action/ajouter/", views.action_plan_form_view, name="action_plan_create"),
    path("plan-action/<int:pk>/modifier/", views.action_plan_form_view, name="action_plan_update"),
    path("plan-action/<int:pk>/supprimer/", views.action_plan_delete, name="action_plan_delete"),

    # Import / export
    path("import-excel/", views.import_excel_view, name="import_excel"),
    path("export/commandes.csv", views.export_orders_csv, name="export_orders_csv"),
    path("export/kpi.xlsx", views.export_kpi_excel, name="export_kpi_excel"),
]
