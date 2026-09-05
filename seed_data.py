"""
Commande : python manage.py seed_data
Génère des données FICTIVES réalistes pour tester l'application.
Ces données sont clairement marquées source='demo' pour ne pas être
confondues avec les données réelles de l'entreprise.
"""
import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from dashboard.models import Supplier, Order, Transport, Transit, Dispute, ActionPlan, Cause


DEMO_SUPPLIERS = [
    ("TransMar Logistics", "FRN-001", "transporteur", "Maritime"),
    ("Atlas Transit", "FRN-002", "transitaire", "Dédouanement"),
    ("RoadLink Maroc", "FRN-003", "transporteur", "Routier"),
    ("AirCargo Express", "FRN-004", "transporteur", "Aérien"),
    ("Sahara Freight", "FRN-005", "transporteur", "Routier"),
    ("PortConnect", "FRN-006", "agent_maritime", "Manutention portuaire"),
    ("MedTrans", "FRN-007", "transporteur", "Maritime"),
    ("Douane Facile", "FRN-008", "transitaire", "Dédouanement"),
]

OVERRUN_CAUSES = ["Frais supplémentaires", "Mauvaise planification", "Attente", "Changement de destination",
                   "Urgence", "Erreur documentaire", "Frais douaniers", "Immobilisation", "Autre"]
DELAY_CAUSES = ["Problème documentaire", "Retard fournisseur", "Problème transport", "Dédouanement",
                "Météo", "Indisponibilité", "Problème administratif", "Autre"]

CITIES = ["Casablanca", "Tanger", "Agadir", "Jorf Lasfar", "Marrakech", "Rabat", "Fès", "Rotterdam", "Shanghai", "Hambourg"]
SERVICE_TYPES = ["maritime", "routier", "aerien", "ferroviaire"]


class Command(BaseCommand):
    help = "Génère des données de démonstration (fictives) pour tester l'application."

    def add_arguments(self, parser):
        parser.add_argument("--orders", type=int, default=60, help="Nombre de commandes fictives à générer")

    def handle(self, *args, **options):
        n_orders = options["orders"]

        # Causes
        causes = {}
        for label in OVERRUN_CAUSES:
            c, _ = Cause.objects.get_or_create(label=label, type="surcout")
            causes[("surcout", label)] = c
        for label in DELAY_CAUSES:
            c, _ = Cause.objects.get_or_create(label=label, type="retard")
            causes[("retard", label)] = c

        # Fournisseurs
        suppliers = []
        for name, code, category, service in DEMO_SUPPLIERS:
            s, _ = Supplier.objects.get_or_create(
                code=code,
                defaults={
                    "name": name, "category": category, "service_type": service,
                    "contact": "Service commercial", "email": f"contact@{code.lower()}.ma",
                    "phone": "0522-000000", "status": "actif",
                },
            )
            suppliers.append(s)

        self.stdout.write(f"{len(suppliers)} fournisseurs de démonstration prêts.")

        created_orders = 0
        for i in range(n_orders):
            supplier = random.choice(suppliers)
            order_date = date(2026, 1, 1) + timedelta(days=random.randint(0, 240))
            planned_date = order_date + timedelta(days=random.randint(5, 20))
            delay = random.choice([0, 0, 0, 1, 2, 3, 5, 7, 10])
            has_actual = random.random() < 0.9
            actual_date = planned_date + timedelta(days=delay) if has_actual else None

            planned_cost = random.randint(40, 450) * 1000
            overrun_pct = random.choice([0, 0, 0.02, 0.05, 0.08, 0.12, 0.18, 0.25])
            actual_cost = round(planned_cost * (1 + overrun_pct)) if has_actual else None

            service_type = random.choice(SERVICE_TYPES)
            origin, destination = random.sample(CITIES, 2)
            status = "livree" if has_actual and delay == 0 else ("retardee" if has_actual and delay > 0 else "en_cours")

            order = Order.objects.create(
                number=f"CMD-DEMO-{2026}-{i+1:04d}",
                declaration_ref=f"DEC-{random.randint(10000,99999)}/2026",
                order_date=order_date,
                supplier=supplier,
                service_type=service_type,
                origin=origin,
                destination=destination,
                planned_date=planned_date,
                actual_date=actual_date,
                planned_cost=planned_cost,
                actual_cost=actual_cost,
                status=status,
                observations="Donnée de démonstration générée automatiquement.",
                source="demo",
            )
            created_orders += 1

            Transport.objects.create(
                reference=f"TR-DEMO-{i+1:04d}",
                order=order,
                supplier=supplier,
                mode=service_type,
                origin=origin,
                destination=destination,
                planned_departure=order_date,
                actual_departure=order_date + timedelta(days=random.randint(0, 2)) if has_actual else None,
                planned_arrival=planned_date,
                actual_arrival=actual_date,
                planned_cost=round(planned_cost * 0.7),
                actual_cost=round(actual_cost * 0.7) if actual_cost else None,
                distance=random.randint(50, 4000),
                quantity=f"{random.randint(1,3)} conteneur(s)" if service_type == "maritime" else f"{random.randint(5,20)} tonnes",
                weight=random.randint(500, 20000),
                status="arrive" if has_actual else "planifie",
            )

            if random.random() < 0.6:
                cause_type = "retard" if delay > 0 else None
                Transit.objects.create(
                    reference=f"TS-DEMO-{i+1:04d}",
                    order=order,
                    supplier=random.choice([s for s in suppliers if s.category == "transitaire"] or suppliers),
                    start_date=order_date,
                    planned_clearance_date=planned_date,
                    actual_clearance_date=actual_date,
                    planned_duration=random.randint(2, 8),
                    actual_duration=random.randint(2, 12) if has_actual else None,
                    fees=round(planned_cost * 0.05),
                    additional_fees=round(planned_cost * 0.02) if overrun_pct > 0 else 0,
                    delay_cause=causes.get(("retard", random.choice(DELAY_CAUSES))) if cause_type else None,
                    status="dedouane" if has_actual else "en_cours",
                )

            if random.random() < 0.15:
                Dispute.objects.create(
                    supplier=supplier,
                    order=order,
                    problem_type=random.choice(["Retard de livraison", "Facturation incorrecte", "Marchandise endommagée", "Documents manquants"]),
                    date=planned_date,
                    description="Litige généré automatiquement pour les besoins de la démonstration.",
                    cost=random.randint(1000, 15000),
                    impact=random.choice(["Faible", "Moyen", "Élevé"]),
                    status=random.choice(["ouvert", "en_cours", "resolu", "clos"]),
                    cause=causes.get(("surcout", random.choice(OVERRUN_CAUSES))) if random.random() < 0.5 else causes.get(("retard", random.choice(DELAY_CAUSES))),
                    corrective_action="Analyse en cours avec le fournisseur." if random.random() < 0.5 else "",
                )

        self.stdout.write(self.style.SUCCESS(f"{created_orders} commandes de démonstration créées (source='demo')."))

        # Plan d'action de démonstration
        if not ActionPlan.objects.exists():
            for supplier in suppliers[:3]:
                ActionPlan.objects.create(
                    problem=f"Taux de retard élevé chez {supplier.name}",
                    supplier=supplier,
                    cause=causes.get(("retard", "Retard fournisseur")),
                    action="Mettre en place un point de suivi hebdomadaire et revoir les délais contractuels.",
                    responsible="Responsable Logistique",
                    start_date=date(2026, 3, 1),
                    deadline=date(2026, 6, 30),
                    priority=random.choice(["moyenne", "haute", "critique"]),
                    status=random.choice(["a_faire", "en_cours"]),
                    expected_result="Réduction du taux de retard de 15 points.",
                )
            self.stdout.write(self.style.SUCCESS("Plan d'action de démonstration créé."))

        self.stdout.write(self.style.WARNING(
            "⚠️  Ces données sont des DONNÉES DE DÉMONSTRATION et ne représentent pas les données réelles de l'entreprise."
        ))
