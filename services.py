"""
Couche de services - Calcul des KPI logistiques

Toutes les formules du cahier des charges y sont centralisées afin de
garder les vues (views.py) légères et le code testable / maintenable.
"""
from decimal import Decimal
from django.conf import settings
from django.db.models import Sum, Count, Q, Avg
from .models import Order, Supplier, Dispute


def _safe_div(a, b):
    a = float(a or 0)
    b = float(b or 0)
    return (a / b) if b else 0.0


def filter_orders(queryset, filters=None):
    """Applique les filtres du dashboard (période, fournisseur, mode, statut, origine, destination)."""
    filters = filters or {}
    if filters.get("supplier"):
        queryset = queryset.filter(supplier_id=filters["supplier"])
    if filters.get("service_type"):
        queryset = queryset.filter(service_type=filters["service_type"])
    if filters.get("status"):
        queryset = queryset.filter(status=filters["status"])
    if filters.get("origin"):
        queryset = queryset.filter(origin__icontains=filters["origin"])
    if filters.get("destination"):
        queryset = queryset.filter(destination__icontains=filters["destination"])
    if filters.get("date_from"):
        queryset = queryset.filter(order_date__gte=filters["date_from"])
    if filters.get("date_to"):
        queryset = queryset.filter(order_date__lte=filters["date_to"])
    return queryset


def compute_global_kpis(orders_qs):
    """Calcule les KPI globaux à partir d'un queryset de commandes."""
    total_orders = orders_qs.count()
    delivered = orders_qs.exclude(actual_date__isnull=True)

    on_time = sum(1 for o in delivered if o.delay_days is not None and o.delay_days <= 0)
    delivered_count = delivered.count()
    otd = round(_safe_div(on_time, delivered_count) * 100, 2) if delivered_count else 0.0

    late_count = sum(1 for o in delivered if o.delay_days is not None and o.delay_days > 0)
    delay_rate = round(_safe_div(late_count, delivered_count) * 100, 2) if delivered_count else 0.0

    total_planned_cost = orders_qs.aggregate(s=Sum("planned_cost"))["s"] or Decimal("0")
    total_actual_cost = orders_qs.exclude(actual_cost__isnull=True).aggregate(s=Sum("actual_cost"))["s"] or Decimal("0")
    cost_gap = total_actual_cost - total_planned_cost
    overrun_rate = round(_safe_div(cost_gap, total_planned_cost) * 100, 2) if total_planned_cost else 0.0

    avg_cost = round(_safe_div(total_actual_cost or total_planned_cost, total_orders), 2) if total_orders else 0.0

    disputes_count = Dispute.objects.filter(order__in=orders_qs).count()
    dispute_rate = round(_safe_div(disputes_count, total_orders) * 100, 2) if total_orders else 0.0

    return {
        "total_orders": total_orders,
        "otd": otd,
        "delay_rate": delay_rate,
        "total_planned_cost": total_planned_cost,
        "total_actual_cost": total_actual_cost or total_planned_cost,
        "cost_gap": cost_gap,
        "overrun_rate": overrun_rate,
        "avg_cost": avg_cost,
        "disputes_count": disputes_count,
        "dispute_rate": dispute_rate,
    }


def compute_supplier_kpis(supplier, orders_qs=None):
    """KPI détaillés pour un fournisseur donné."""
    orders_qs = orders_qs if orders_qs is not None else Order.objects.filter(supplier=supplier)
    kpis = compute_global_kpis(orders_qs)
    kpis["supplier"] = supplier
    kpis["score"] = compute_supplier_score(kpis)
    return kpis


def compute_supplier_score(kpis):
    """
    Score fournisseur configurable (0-100) :
        40% OTD + 30% maîtrise des coûts + 20% qualité de service + 10% absence de litiges
    La maîtrise des coûts est d'autant meilleure que le taux de surcoût est bas.
    La "qualité de service" est approximée ici par l'inverse du taux de retard
    (peut être enrichie plus tard avec des critères qualitatifs additionnels).
    """
    weights = settings.SCORE_WEIGHTS
    otd_score = kpis["otd"]
    cost_score = max(0.0, 100 - min(kpis["overrun_rate"], 100) * 2) if kpis["overrun_rate"] > 0 else 100.0
    quality_score = max(0.0, 100 - kpis["delay_rate"])
    dispute_score = max(0.0, 100 - kpis["dispute_rate"] * 5)

    score = (
        otd_score * weights["otd"]
        + cost_score * weights["cost_control"]
        + quality_score * weights["quality"]
        + dispute_score * weights["no_disputes"]
    )
    return round(score, 1)


def score_badge(score):
    if score >= 75:
        return ("Excellent", "success", "🟢")
    if score >= 50:
        return ("Moyen", "warning", "🟡")
    return ("À améliorer", "danger", "🔴")


def rank_suppliers(orders_qs=None):
    """Retourne la liste des fournisseurs classés par score décroissant."""
    results = []
    for supplier in Supplier.objects.all():
        qs = orders_qs.filter(supplier=supplier) if orders_qs is not None else Order.objects.filter(supplier=supplier)
        if not qs.exists():
            continue
        kpis = compute_supplier_kpis(supplier, qs)
        badge = score_badge(kpis["score"])
        results.append({**kpis, "badge_label": badge[0], "badge_color": badge[1], "badge_icon": badge[2]})
    results.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(results, start=1):
        r["rank"] = i
    return results


def top_suppliers_by_overrun(orders_qs=None, limit=5):
    ranking = rank_suppliers(orders_qs)
    return sorted(ranking, key=lambda r: r["overrun_rate"], reverse=True)[:limit]


def top_performing_suppliers(orders_qs=None, limit=5):
    ranking = rank_suppliers(orders_qs)
    return ranking[:limit]


def overrun_analysis(orders_qs):
    """Tableau d'analyse des surcoûts par fournisseur."""
    rows = []
    suppliers = Supplier.objects.filter(orders__in=orders_qs).distinct()
    for supplier in suppliers:
        qs = orders_qs.filter(supplier=supplier).exclude(actual_cost__isnull=True)
        if not qs.exists():
            continue
        planned = qs.aggregate(s=Sum("planned_cost"))["s"] or Decimal("0")
        actual = qs.aggregate(s=Sum("actual_cost"))["s"] or Decimal("0")
        gap = actual - planned
        rate = round(_safe_div(gap, planned) * 100, 2) if planned else 0.0
        rows.append({
            "supplier": supplier,
            "planned_cost": planned,
            "actual_cost": actual,
            "gap": gap,
            "rate": rate,
        })
    rows.sort(key=lambda r: r["gap"], reverse=True)
    return rows


def delay_analysis(orders_qs):
    """Tableau d'analyse des retards par fournisseur."""
    rows = []
    suppliers = Supplier.objects.filter(orders__in=orders_qs).distinct()
    for supplier in suppliers:
        qs = orders_qs.filter(supplier=supplier).exclude(actual_date__isnull=True)
        if not qs.exists():
            continue
        total = qs.count()
        delays = [o.delay_days for o in qs if o.delay_days is not None and o.delay_days > 0]
        late_count = len(delays)
        avg_delay = round(sum(delays) / late_count, 1) if late_count else 0.0
        rate = round(_safe_div(late_count, total) * 100, 2)
        rows.append({
            "supplier": supplier,
            "total_orders": total,
            "late_orders": late_count,
            "delay_rate": rate,
            "avg_delay": avg_delay,
        })
    rows.sort(key=lambda r: r["delay_rate"], reverse=True)
    return rows


def generate_recommendations(orders_qs):
    """Génère des recommandations textuelles à partir des KPI réellement calculés."""
    recos = []
    global_kpis = compute_global_kpis(orders_qs)

    if global_kpis["otd"] < 80 and orders_qs.exists():
        recos.append({
            "level": "danger",
            "title": "Performance de livraison insuffisante",
            "text": (
                f"L'OTD global est de {global_kpis['otd']}%, en dessous du seuil de 80%. "
                "Il est recommandé de mettre en place un suivi renforcé des fournisseurs concernés "
                "et d'étudier en détail les causes des retards."
            ),
        })

    if global_kpis["overrun_rate"] > 10:
        recos.append({
            "level": "warning",
            "title": "Niveau de surcoût élevé",
            "text": (
                f"Le taux de surcoût global atteint {global_kpis['overrun_rate']}%. "
                "Une analyse détaillée des coûts supplémentaires et des conditions contractuelles "
                "avec les fournisseurs concernés est recommandée."
            ),
        })

    if global_kpis["dispute_rate"] > 5:
        recos.append({
            "level": "warning",
            "title": "Taux de litiges préoccupant",
            "text": (
                f"{global_kpis['dispute_rate']}% des commandes ont donné lieu à un litige. "
                "Un renforcement des clauses contractuelles et des points de contrôle qualité est conseillé."
            ),
        })

    # Recommandations par fournisseur en difficulté
    for row in rank_suppliers(orders_qs):
        if row["score"] < 50:
            recos.append({
                "level": "danger",
                "title": f"Fournisseur à surveiller : {row['supplier'].name}",
                "text": (
                    f"Score de performance de {row['score']}/100 (OTD {row['otd']}%, "
                    f"taux de surcoût {row['overrun_rate']}%). "
                    "Une revue de performance avec ce fournisseur est recommandée."
                ),
            })

    if not recos:
        recos.append({
            "level": "success",
            "title": "Performance globale satisfaisante",
            "text": "Aucun seuil critique n'est actuellement dépassé sur les données disponibles.",
        })

    return recos


def cause_breakdown(model, cause_type):
    """Répartition des causes de retard ou de surcoût (pour les litiges/transit)."""
    from .models import Dispute as DisputeModel
    qs = DisputeModel.objects.filter(cause__type=cause_type).values("cause__label").annotate(total=Count("id")).order_by("-total")
    return list(qs)
