"""
Modèles de données - IMACID Logistics Performance

Architecture :
    Supplier (Fournisseur)
        └── Order (Commande)
                ├── Transport
                ├── Transit
                └── Dispute (Litige)
    Cause (référentiel des causes de retard / surcoût)
    ActionPlan (Plan d'action correctif)
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Supplier(models.Model):
    CATEGORY_CHOICES = [
        ("transporteur", "Transporteur"),
        ("transitaire", "Transitaire"),
        ("agent_maritime", "Agent maritime"),
        ("autre", "Autre"),
    ]
    STATUS_CHOICES = [
        ("actif", "Actif"),
        ("inactif", "Inactif"),
        ("suspendu", "Suspendu"),
    ]

    name = models.CharField("Nom", max_length=150)
    code = models.CharField("Code fournisseur", max_length=30, unique=True)
    category = models.CharField("Catégorie", max_length=30, choices=CATEGORY_CHOICES, default="transporteur")
    service_type = models.CharField("Type de prestation", max_length=100, blank=True)
    contact = models.CharField("Contact", max_length=150, blank=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=30, blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="actif")
    notes = models.TextField("Observations", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse("supplier_detail", args=[self.pk])


class Cause(models.Model):
    TYPE_CHOICES = [
        ("surcout", "Surcoût"),
        ("retard", "Retard"),
    ]
    label = models.CharField("Libellé", max_length=150)
    type = models.CharField("Type", max_length=20, choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Cause"
        verbose_name_plural = "Causes"
        ordering = ["type", "label"]

    def __str__(self):
        return f"{self.get_type_display()} - {self.label}"


class Order(models.Model):
    SERVICE_CHOICES = [
        ("maritime", "Maritime"),
        ("routier", "Routier"),
        ("aerien", "Aérien"),
        ("ferroviaire", "Ferroviaire"),
    ]
    STATUS_CHOICES = [
        ("en_cours", "En cours"),
        ("livree", "Livrée"),
        ("retardee", "Retardée"),
        ("annulee", "Annulée"),
    ]
    SOURCE_CHOICES = [
        ("reelle", "Donnée réelle"),
        ("demo", "Donnée de démonstration"),
    ]

    number = models.CharField("Numéro de commande", max_length=50, unique=True)
    declaration_ref = models.CharField("Référence déclaration", max_length=50, blank=True)
    order_date = models.DateField("Date de commande")
    supplier = models.ForeignKey(Supplier, verbose_name="Fournisseur", on_delete=models.CASCADE, related_name="orders")
    service_type = models.CharField("Type de prestation", max_length=20, choices=SERVICE_CHOICES, default="routier")
    origin = models.CharField("Origine", max_length=150)
    destination = models.CharField("Destination", max_length=150)
    planned_date = models.DateField("Date prévue")
    actual_date = models.DateField("Date réelle", null=True, blank=True)
    planned_cost = models.DecimalField("Coût prévu (MAD)", max_digits=14, decimal_places=2)
    actual_cost = models.DecimalField("Coût réel (MAD)", max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="en_cours")
    observations = models.TextField("Observations", blank=True)
    source = models.CharField("Origine des données", max_length=10, choices=SOURCE_CHOICES, default="demo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-order_date"]

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse("order_detail", args=[self.pk])

    @property
    def delay_days(self):
        if self.actual_date and self.planned_date:
            return (self.actual_date - self.planned_date).days
        return None

    @property
    def is_late(self):
        d = self.delay_days
        return d is not None and d > 0

    @property
    def cost_gap(self):
        if self.actual_cost is not None:
            return self.actual_cost - self.planned_cost
        return None

    @property
    def cost_overrun_rate(self):
        gap = self.cost_gap
        if gap is not None and self.planned_cost:
            return round(float(gap) / float(self.planned_cost) * 100, 2)
        return None


class Transport(models.Model):
    MODE_CHOICES = [
        ("maritime", "Maritime"),
        ("routier", "Routier"),
        ("aerien", "Aérien"),
        ("ferroviaire", "Ferroviaire"),
    ]
    STATUS_CHOICES = [
        ("planifie", "Planifié"),
        ("en_transit", "En transit"),
        ("arrive", "Arrivé"),
        ("retarde", "Retardé"),
    ]

    reference = models.CharField("Référence transport", max_length=50, unique=True)
    order = models.ForeignKey(Order, verbose_name="Commande", on_delete=models.CASCADE, related_name="transports")
    supplier = models.ForeignKey(Supplier, verbose_name="Fournisseur", on_delete=models.CASCADE, related_name="transports")
    mode = models.CharField("Mode de transport", max_length=20, choices=MODE_CHOICES)
    origin = models.CharField("Origine", max_length=150)
    destination = models.CharField("Destination", max_length=150)
    planned_departure = models.DateField("Date de départ prévue", null=True, blank=True)
    actual_departure = models.DateField("Date de départ réelle", null=True, blank=True)
    planned_arrival = models.DateField("Date d'arrivée prévue", null=True, blank=True)
    actual_arrival = models.DateField("Date d'arrivée réelle", null=True, blank=True)
    planned_cost = models.DecimalField("Coût prévu (MAD)", max_digits=14, decimal_places=2)
    actual_cost = models.DecimalField("Coût réel (MAD)", max_digits=14, decimal_places=2, null=True, blank=True)
    distance = models.FloatField("Distance (km)", null=True, blank=True)
    quantity = models.CharField("Quantité / Contenants", max_length=100, blank=True)
    weight = models.FloatField("Poids (kg)", null=True, blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="planifie")

    class Meta:
        verbose_name = "Transport"
        verbose_name_plural = "Transports"
        ordering = ["-planned_departure"]

    def __str__(self):
        return self.reference


class Transit(models.Model):
    STATUS_CHOICES = [
        ("en_cours", "En cours"),
        ("dedouane", "Dédouané"),
        ("bloque", "Bloqué"),
        ("retarde", "Retardé"),
    ]

    reference = models.CharField("Référence transit", max_length=50, unique=True)
    order = models.ForeignKey(Order, verbose_name="Commande", on_delete=models.CASCADE, related_name="transits")
    supplier = models.ForeignKey(Supplier, verbose_name="Fournisseur / Transitaire", on_delete=models.CASCADE, related_name="transits")
    start_date = models.DateField("Date de début", null=True, blank=True)
    planned_clearance_date = models.DateField("Date prévue de dédouanement", null=True, blank=True)
    actual_clearance_date = models.DateField("Date réelle de dédouanement", null=True, blank=True)
    planned_duration = models.IntegerField("Durée prévue (jours)", null=True, blank=True)
    actual_duration = models.IntegerField("Durée réelle (jours)", null=True, blank=True)
    fees = models.DecimalField("Frais de transit (MAD)", max_digits=14, decimal_places=2, default=0)
    additional_fees = models.DecimalField("Frais supplémentaires (MAD)", max_digits=14, decimal_places=2, default=0)
    delay_cause = models.ForeignKey(Cause, verbose_name="Cause du retard", on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={"type": "retard"})
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="en_cours")

    class Meta:
        verbose_name = "Transit"
        verbose_name_plural = "Transits"
        ordering = ["-start_date"]

    def __str__(self):
        return self.reference


class Dispute(models.Model):
    STATUS_CHOICES = [
        ("ouvert", "Ouvert"),
        ("en_cours", "En cours de traitement"),
        ("resolu", "Résolu"),
        ("clos", "Clos"),
    ]
    supplier = models.ForeignKey(Supplier, verbose_name="Fournisseur", on_delete=models.CASCADE, related_name="disputes")
    order = models.ForeignKey(Order, verbose_name="Commande", on_delete=models.CASCADE, related_name="disputes", null=True, blank=True)
    problem_type = models.CharField("Type de problème", max_length=150)
    date = models.DateField("Date")
    description = models.TextField("Description", blank=True)
    cost = models.DecimalField("Coût du litige (MAD)", max_digits=14, decimal_places=2, default=0)
    impact = models.CharField("Impact", max_length=150, blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="ouvert")
    cause = models.ForeignKey(Cause, verbose_name="Cause", on_delete=models.SET_NULL, null=True, blank=True)
    corrective_action = models.TextField("Action corrective", blank=True)

    class Meta:
        verbose_name = "Litige"
        verbose_name_plural = "Litiges"
        ordering = ["-date"]

    def __str__(self):
        return f"Litige {self.supplier} - {self.problem_type}"


class ActionPlan(models.Model):
    PRIORITY_CHOICES = [
        ("faible", "Faible"),
        ("moyenne", "Moyenne"),
        ("haute", "Haute"),
        ("critique", "Critique"),
    ]
    STATUS_CHOICES = [
        ("a_faire", "À faire"),
        ("en_cours", "En cours"),
        ("realise", "Réalisé"),
        ("annule", "Annulé"),
    ]

    problem = models.CharField("Problème identifié", max_length=255)
    supplier = models.ForeignKey(Supplier, verbose_name="Fournisseur concerné", on_delete=models.CASCADE, related_name="action_plans", null=True, blank=True)
    cause = models.ForeignKey(Cause, verbose_name="Cause", on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField("Action proposée")
    responsible = models.CharField("Responsable", max_length=150)
    start_date = models.DateField("Date de début")
    deadline = models.DateField("Date limite")
    priority = models.CharField("Priorité", max_length=20, choices=PRIORITY_CHOICES, default="moyenne")
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default="a_faire")
    expected_result = models.TextField("Résultat attendu", blank=True)
    comment = models.TextField("Commentaire", blank=True)

    class Meta:
        verbose_name = "Action du plan"
        verbose_name_plural = "Plan d'action"
        ordering = ["-priority", "deadline"]

    def __str__(self):
        return self.problem
