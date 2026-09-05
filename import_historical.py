"""
Commande : python manage.py import_historical
Importe les 10 commandes réelles du rapport "Données Historiques 2026"
(exercice 2026) fourni par l'entreprise. Ces commandes sont marquées
source='reelle' pour bien les distinguer des données de démonstration.
"""
from datetime import date

from django.core.management.base import BaseCommand
from dashboard.models import Supplier, Order, Transport, Cause


# Données extraites du rapport "DONNÉES HISTORIQUES - Rapport Logistique 2026"
HISTORICAL_ORDERS = [
    dict(number="CMD-2024-001", declaration_ref="DEC-10293/2007", order_date=date(2026,1,5), actual_date=date(2026,1,12),
         supplier_name="SAPI", port="CASA PORT", mode="maritime", qty="1 Container",
         caf=150000.00, taxes=32500.00, transport=12000.00, transit=3500.00),
    dict(number="CMD-2024-002", declaration_ref="DEC-10450/2007", order_date=date(2026,1,10), actual_date=date(2026,1,15),
         supplier_name="NEGOCOL GRAIN", port="CASA MELLALL", mode="routier", qty="15 Tonnes",
         caf=280000.00, taxes=45000.00, transport=8500.00, transit=2800.00),
    dict(number="CMD-2024-003", declaration_ref="DEC-02194/2010", order_date=date(2026,1,18), actual_date=date(2026,1,26),
         supplier_name="HAWORLD", port="CASA PORT", mode="maritime", qty="2 Containers",
         caf=420000.00, taxes=89000.00, transport=22000.00, transit=5200.00),
    dict(number="CMD-2024-004", declaration_ref="DEC-01120/2011", order_date=date(2026,2,10), actual_date=date(2026,2,17),
         supplier_name="MALEIXEL OMAR", port="CASA APM", mode="aerien", qty="850 kg",
         caf=95000.00, taxes=18200.00, transport=14500.00, transit=4100.00),
    dict(number="CMD-2024-005", declaration_ref="DEC-01850/2011", order_date=date(2026,2,20), actual_date=date(2026,2,28),
         supplier_name="AFARI", port="WAFA", mode="routier", qty="8 Tonnes",
         caf=110000.00, taxes=21000.00, transport=6000.00, transit=2200.00),
    dict(number="CMD-2024-006", declaration_ref="DEC-02410/2011", order_date=date(2026,2,26), actual_date=date(2026,3,5),
         supplier_name="HA CHITHIL OMA", port="TANGER MED", mode="maritime", qty="1 Container",
         caf=310000.00, taxes=65000.00, transport=18500.00, transit=4800.00),
    dict(number="CMD-2024-007", declaration_ref="DEC-03105/2011", order_date=date(2026,3,4), actual_date=date(2026,3,12),
         supplier_name="SAP AFTOD", port="CASA PORT", mode="maritime", qty="1 Container",
         caf=185000.00, taxes=38000.00, transport=12500.00, transit=3600.00),
    dict(number="CMD-2024-008", declaration_ref="DEC-04520/2011", order_date=date(2026,3,22), actual_date=date(2026,3,30),
         supplier_name="ERRABHI HON", port="AGADIR PORT", mode="routier", qty="12 Tonnes",
         caf=230000.00, taxes=41000.00, transport=9200.00, transit=3100.00),
    dict(number="CMD-2024-009", declaration_ref="DEC-05890/2011", order_date=date(2026,4,8), actual_date=date(2026,4,18),
         supplier_name="CASA WAFA SA", port="CASA PORT", mode="maritime", qty="1 Container",
         caf=290000.00, taxes=58000.00, transport=16000.00, transit=4500.00),
    dict(number="CMD-2024-010", declaration_ref="DEC-07210/2011", order_date=date(2026,5,1), actual_date=date(2026,5,10),
         supplier_name="SAPI DISTRIBUTION", port="TANGER MED", mode="maritime", qty="1 Container",
         caf=165000.00, taxes=34000.00, transport=11800.00, transit=3400.00),
]


class Command(BaseCommand):
    help = "Importe les données historiques réelles 2026 (rapport logistique fourni par l'entreprise)."

    def handle(self, *args, **options):
        created = 0
        for row in HISTORICAL_ORDERS:
            supplier, _ = Supplier.objects.get_or_create(
                code=row["supplier_name"][:20].upper().replace(" ", "-"),
                defaults={
                    "name": row["supplier_name"],
                    "category": "transporteur",
                    "status": "actif",
                },
            )

            planned_cost = row["transport"] + row["transit"]
            # Pas d'écart connu entre prévu/réel dans le rapport source : coût réel = coût constaté
            actual_cost = planned_cost
            planned_date = row["order_date"]

            order, was_created = Order.objects.update_or_create(
                number=row["number"],
                defaults=dict(
                    declaration_ref=row["declaration_ref"],
                    order_date=row["order_date"],
                    supplier=supplier,
                    service_type=row["mode"],
                    origin=row["port"],
                    destination="Client final",
                    planned_date=planned_date,
                    actual_date=row["actual_date"],
                    planned_cost=planned_cost,
                    actual_cost=actual_cost,
                    status="livree",
                    observations=(
                        f"Valeur CAF : {row['caf']:.2f} MAD — Droits & taxes : {row['taxes']:.2f} MAD. "
                        "Donnée historique réelle (exercice 2026)."
                    ),
                    source="reelle",
                ),
            )
            if was_created:
                created += 1

            Transport.objects.update_or_create(
                reference=f"TR-{row['number']}",
                defaults=dict(
                    order=order,
                    supplier=supplier,
                    mode=row["mode"],
                    origin=row["port"],
                    destination="Client final",
                    planned_departure=row["order_date"],
                    actual_departure=row["order_date"],
                    planned_arrival=row["actual_date"],
                    actual_arrival=row["actual_date"],
                    planned_cost=row["transport"],
                    actual_cost=row["transport"],
                    quantity=row["qty"],
                    status="arrive",
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            f"{created} commande(s) réelle(s) importée(s) depuis le rapport 'Données Historiques 2026' (source='reelle')."
        ))
