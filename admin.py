from django.contrib import admin
from .models import Supplier, Order, Transport, Transit, Dispute, ActionPlan, Cause


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "category", "status", "service_type"]
    list_filter = ["category", "status"]
    search_fields = ["name", "code"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["number", "supplier", "order_date", "planned_date", "actual_date", "status", "planned_cost", "actual_cost", "source"]
    list_filter = ["status", "service_type", "source", "supplier"]
    search_fields = ["number", "declaration_ref"]
    date_hierarchy = "order_date"


@admin.register(Transport)
class TransportAdmin(admin.ModelAdmin):
    list_display = ["reference", "order", "supplier", "mode", "status", "planned_cost", "actual_cost"]
    list_filter = ["mode", "status"]
    search_fields = ["reference"]


@admin.register(Transit)
class TransitAdmin(admin.ModelAdmin):
    list_display = ["reference", "order", "supplier", "status", "fees", "additional_fees"]
    list_filter = ["status"]
    search_fields = ["reference"]


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ["supplier", "order", "problem_type", "date", "cost", "status"]
    list_filter = ["status", "cause"]


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ["problem", "supplier", "priority", "status", "deadline", "responsible"]
    list_filter = ["priority", "status"]


@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
    list_display = ["label", "type"]
    list_filter = ["type"]
