"""
Vues - IMACID Logistics Performance
"""
import csv
import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from . import services
from .forms import (
    OrderForm, SupplierForm, TransportForm, TransitForm,
    DisputeForm, ActionPlanForm, ExcelImportForm,
)
from .models import Order, Supplier, Transport, Transit, Dispute, ActionPlan, Cause


class DecimalEncoder(json.JSONEncoder):
    """Permet de sérialiser les montants Decimal des modèles Django en JSON."""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def _to_json(value):
    return json.dumps(value, cls=DecimalEncoder, ensure_ascii=False)


class ImacidLoginView(LoginView):
    template_name = "registration/login.html"


def _get_filters(request):
    return {
        "supplier": request.GET.get("supplier") or "",
        "service_type": request.GET.get("service_type") or "",
        "status": request.GET.get("status") or "",
        "origin": request.GET.get("origin") or "",
        "destination": request.GET.get("destination") or "",
        "date_from": request.GET.get("date_from") or "",
        "date_to": request.GET.get("date_to") or "",
    }


@login_required
def dashboard_view(request):
    filters = _get_filters(request)
    orders_qs = services.filter_orders(Order.objects.all(), filters)

    kpis = services.compute_global_kpis(orders_qs)
    ranking = services.rank_suppliers(orders_qs)
    avg_score = round(sum(r["score"] for r in ranking) / len(ranking), 1) if ranking else 0.0

    # Séries pour les graphiques
    monthly = (
        orders_qs.exclude(actual_cost__isnull=True)
        .values("order_date__year", "order_date__month")
        .annotate(planned=Sum("planned_cost"), actual=Sum("actual_cost"), n=Count("id"))
        .order_by("order_date__year", "order_date__month")
    )
    months_labels = [f"{m['order_date__month']:02d}/{m['order_date__year']}" for m in monthly]
    months_planned = [float(m["planned"] or 0) for m in monthly]
    months_actual = [float(m["actual"] or 0) for m in monthly]

    delay_analysis = services.delay_analysis(orders_qs)
    overrun_analysis = services.overrun_analysis(orders_qs)
    top_perf = services.top_performing_suppliers(orders_qs, limit=5)
    top_overrun = services.top_suppliers_by_overrun(orders_qs, limit=5)

    overrun_causes = services.cause_breakdown(Dispute, "surcout")
    delay_causes = services.cause_breakdown(Dispute, "retard")
    for c in overrun_causes + delay_causes:
        if not c.get("cause__label"):
            c["cause__label"] = "Non renseignée"

    context = {
        "kpis": kpis,
        "avg_score": avg_score,
        "suppliers": Supplier.objects.all(),
        "filters": filters,
        "months_labels_json": _to_json(months_labels),
        "months_planned_json": _to_json(months_planned),
        "months_actual_json": _to_json(months_actual),
        "delay_labels_json": _to_json([r["supplier"].name for r in delay_analysis[:8]]),
        "delay_values_json": _to_json([r["late_orders"] for r in delay_analysis[:8]]),
        "otd_labels_json": _to_json([r["supplier"].name for r in ranking[:8]]),
        "otd_values_json": _to_json([r["otd"] for r in ranking[:8]]),
        "score_labels_json": _to_json([r["supplier"].name for r in ranking[:8]]),
        "score_values_json": _to_json([r["score"] for r in ranking[:8]]),
        "planned_total_json": _to_json(float(kpis["total_planned_cost"])),
        "actual_total_json": _to_json(float(kpis["total_actual_cost"])),
        "top_perf": top_perf,
        "top_overrun": top_overrun,
        "overrun_causes_labels_json": _to_json([c["cause__label"] for c in overrun_causes]),
        "overrun_causes_values_json": _to_json([c["total"] for c in overrun_causes]),
        "delay_causes_labels_json": _to_json([c["cause__label"] for c in delay_causes]),
        "delay_causes_values_json": _to_json([c["total"] for c in delay_causes]),
        "service_choices": Order.SERVICE_CHOICES,
        "status_choices": Order.STATUS_CHOICES,
    }
    return render(request, "dashboard/dashboard.html", context)


# ---------------------------------------------------------------------------
# CRUD générique simplifié (Commandes, Fournisseurs, Transport, Transit, Litiges, Plan d'action)
# ---------------------------------------------------------------------------

@login_required
def order_list(request):
    q = request.GET.get("q", "")
    orders = Order.objects.select_related("supplier").all()
    if q:
        orders = orders.filter(number__icontains=q)
    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)
    return render(request, "dashboard/order_list.html", {"orders": orders, "q": q, "status_choices": Order.STATUS_CHOICES})


@login_required
def order_form_view(request, pk=None):
    instance = get_object_or_404(Order, pk=pk) if pk else None
    if request.method == "POST":
        form = OrderForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Commande enregistrée avec succès.")
            return redirect("order_list")
    else:
        form = OrderForm(instance=instance)
    return render(request, "dashboard/order_form.html", {"form": form, "instance": instance})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, "Commande supprimée.")
    return redirect("order_list")


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, "dashboard/order_detail.html", {"order": order})


@login_required
def supplier_list(request):
    ranking = {r["supplier"].id: r for r in services.rank_suppliers()}
    suppliers = Supplier.objects.all()
    rows = []
    for s in suppliers:
        r = ranking.get(s.id)
        rows.append({"supplier": s, "kpis": r})
    return render(request, "dashboard/supplier_list.html", {"rows": rows})


@login_required
def supplier_form_view(request, pk=None):
    instance = get_object_or_404(Supplier, pk=pk) if pk else None
    if request.method == "POST":
        form = SupplierForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur enregistré avec succès.")
            return redirect("supplier_list")
    else:
        form = SupplierForm(instance=instance)
    return render(request, "dashboard/supplier_form.html", {"form": form, "instance": instance})


@login_required
def supplier_delete(request, pk):
    get_object_or_404(Supplier, pk=pk).delete()
    messages.success(request, "Fournisseur supprimé.")
    return redirect("supplier_list")


@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    kpis = services.compute_supplier_kpis(supplier)
    badge = services.score_badge(kpis["score"])
    orders = Order.objects.filter(supplier=supplier).order_by("-order_date")
    disputes = Dispute.objects.filter(supplier=supplier)
    return render(request, "dashboard/supplier_detail.html", {
        "supplier": supplier, "kpis": kpis, "badge": badge, "orders": orders, "disputes": disputes,
    })


@login_required
def transport_list(request):
    transports = Transport.objects.select_related("order", "supplier").all()
    return render(request, "dashboard/transport_list.html", {"transports": transports})


@login_required
def transport_form_view(request, pk=None):
    instance = get_object_or_404(Transport, pk=pk) if pk else None
    if request.method == "POST":
        form = TransportForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Transport enregistré.")
            return redirect("transport_list")
    else:
        form = TransportForm(instance=instance)
    return render(request, "dashboard/transport_form.html", {"form": form, "instance": instance})


@login_required
def transport_delete(request, pk):
    get_object_or_404(Transport, pk=pk).delete()
    messages.success(request, "Transport supprimé.")
    return redirect("transport_list")


@login_required
def transit_list(request):
    transits = Transit.objects.select_related("order", "supplier").all()
    return render(request, "dashboard/transit_list.html", {"transits": transits})


@login_required
def transit_form_view(request, pk=None):
    instance = get_object_or_404(Transit, pk=pk) if pk else None
    if request.method == "POST":
        form = TransitForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Transit enregistré.")
            return redirect("transit_list")
    else:
        form = TransitForm(instance=instance)
    return render(request, "dashboard/transit_form.html", {"form": form, "instance": instance})


@login_required
def transit_delete(request, pk):
    get_object_or_404(Transit, pk=pk).delete()
    messages.success(request, "Transit supprimé.")
    return redirect("transit_list")


@login_required
def dispute_list(request):
    disputes = Dispute.objects.select_related("supplier", "order").all()
    return render(request, "dashboard/dispute_list.html", {"disputes": disputes})


@login_required
def dispute_form_view(request, pk=None):
    instance = get_object_or_404(Dispute, pk=pk) if pk else None
    if request.method == "POST":
        form = DisputeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Litige enregistré.")
            return redirect("dispute_list")
    else:
        form = DisputeForm(instance=instance)
    return render(request, "dashboard/dispute_form.html", {"form": form, "instance": instance})


@login_required
def dispute_delete(request, pk):
    get_object_or_404(Dispute, pk=pk).delete()
    messages.success(request, "Litige supprimé.")
    return redirect("dispute_list")


@login_required
def kpi_view(request):
    filters = _get_filters(request)
    orders_qs = services.filter_orders(Order.objects.all(), filters)
    kpis = services.compute_global_kpis(orders_qs)
    ranking = services.rank_suppliers(orders_qs)
    return render(request, "dashboard/kpi.html", {"kpis": kpis, "ranking": ranking, "filters": filters, "suppliers": Supplier.objects.all()})


@login_required
def analysis_overrun_view(request):
    orders_qs = Order.objects.all()
    rows = services.overrun_analysis(orders_qs)
    causes = services.cause_breakdown(Dispute, "surcout")
    return render(request, "dashboard/analysis_overrun.html", {"rows": rows, "causes": causes})


@login_required
def analysis_delay_view(request):
    orders_qs = Order.objects.all()
    rows = services.delay_analysis(orders_qs)
    causes = services.cause_breakdown(Dispute, "retard")
    return render(request, "dashboard/analysis_delay.html", {"rows": rows, "causes": causes})


@login_required
def supplier_ranking_view(request):
    ranking = services.rank_suppliers()
    return render(request, "dashboard/supplier_ranking.html", {"ranking": ranking})


@login_required
def recommendations_view(request):
    recos = services.generate_recommendations(Order.objects.all())
    return render(request, "dashboard/recommendations.html", {"recos": recos})


@login_required
def action_plan_list(request):
    actions = ActionPlan.objects.select_related("supplier", "cause").all()
    total = actions.count()
    done = actions.filter(status="realise").count()
    progress = round(done / total * 100, 1) if total else 0.0
    return render(request, "dashboard/action_plan_list.html", {"actions": actions, "progress": progress})


@login_required
def action_plan_form_view(request, pk=None):
    instance = get_object_or_404(ActionPlan, pk=pk) if pk else None
    if request.method == "POST":
        form = ActionPlanForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Action enregistrée.")
            return redirect("action_plan_list")
    else:
        form = ActionPlanForm(instance=instance)
    return render(request, "dashboard/action_plan_form.html", {"form": form, "instance": instance})


@login_required
def action_plan_delete(request, pk):
    get_object_or_404(ActionPlan, pk=pk).delete()
    messages.success(request, "Action supprimée.")
    return redirect("action_plan_list")


# ---------------------------------------------------------------------------
# Import / Export
# ---------------------------------------------------------------------------

@login_required
def import_excel_view(request):
    preview_rows = None
    errors = []
    if request.method == "POST":
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            import pandas as pd
            fichier = request.FILES["fichier"]
            try:
                df = pd.read_excel(fichier)
            except Exception as exc:
                errors.append(f"Impossible de lire le fichier : {exc}")
                df = None

            required_cols = {"number", "supplier_code", "order_date", "planned_date", "planned_cost"}
            if df is not None:
                missing = required_cols - set(df.columns)
                if missing:
                    errors.append(
                        "Colonnes obligatoires manquantes : " + ", ".join(sorted(missing)) +
                        ". Colonnes attendues : number, supplier_code, order_date, planned_date, "
                        "actual_date, planned_cost, actual_cost, origin, destination, service_type, status."
                    )
                else:
                    created, skipped = 0, 0
                    for _, row in df.iterrows():
                        try:
                            supplier, _ = Supplier.objects.get_or_create(
                                code=str(row["supplier_code"]),
                                defaults={"name": str(row.get("supplier_name", row["supplier_code"]))},
                            )
                            Order.objects.update_or_create(
                                number=str(row["number"]),
                                defaults={
                                    "supplier": supplier,
                                    "order_date": pd.to_datetime(row["order_date"]).date(),
                                    "planned_date": pd.to_datetime(row["planned_date"]).date(),
                                    "actual_date": pd.to_datetime(row["actual_date"]).date() if pd.notna(row.get("actual_date")) else None,
                                    "planned_cost": row["planned_cost"],
                                    "actual_cost": row.get("actual_cost") if pd.notna(row.get("actual_cost")) else None,
                                    "origin": row.get("origin", ""),
                                    "destination": row.get("destination", ""),
                                    "service_type": row.get("service_type", "routier"),
                                    "status": row.get("status", "en_cours"),
                                    "source": "reelle",
                                },
                            )
                            created += 1
                        except Exception as exc:
                            skipped += 1
                            errors.append(f"Ligne ignorée ({row.get('number', '?')}) : {exc}")
                    if created:
                        messages.success(request, f"{created} commande(s) importée(s) avec succès.")
                    preview_rows = df.head(10).to_dict("records")
        else:
            errors.append("Veuillez sélectionner un fichier Excel valide.")
    else:
        form = ExcelImportForm()
    return render(request, "dashboard/import_excel.html", {"form": form, "errors": errors, "preview_rows": preview_rows})


@login_required
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="commandes.csv"'
    writer = csv.writer(response)
    writer.writerow(["Numéro", "Fournisseur", "Date commande", "Date prévue", "Date réelle", "Coût prévu", "Coût réel", "Statut"])
    for o in Order.objects.select_related("supplier").all():
        writer.writerow([o.number, o.supplier.name, o.order_date, o.planned_date, o.actual_date or "", o.planned_cost, o.actual_cost or "", o.get_status_display()])
    return response


@login_required
def export_kpi_excel(request):
    import pandas as pd
    ranking = services.rank_suppliers()
    data = [{
        "Rang": r["rank"], "Fournisseur": r["supplier"].name, "OTD (%)": r["otd"],
        "Taux de retard (%)": r["delay_rate"], "Taux de surcoût (%)": r["overrun_rate"],
        "Litiges": r["disputes_count"], "Score": r["score"],
    } for r in ranking]
    df = pd.DataFrame(data)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="kpi_fournisseurs.xlsx"'
    df.to_excel(response, index=False)
    return response
