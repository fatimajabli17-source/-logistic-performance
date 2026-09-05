"""
Commande : python manage.py create_test_accounts
Crée les 3 comptes de test (Administrateur, Gestionnaire, Utilisateur)
avec les groupes de permissions associés.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission


class Command(BaseCommand):
    help = "Crée les comptes de test et les groupes de permissions (Administrateur / Gestionnaire / Utilisateur)."

    def handle(self, *args, **options):
        gestionnaire_group, _ = Group.objects.get_or_create(name="Gestionnaire")
        utilisateur_group, _ = Group.objects.get_or_create(name="Utilisateur")

        # Le groupe "Gestionnaire" reçoit les droits de gestion des données métier
        app_permissions = Permission.objects.filter(content_type__app_label="dashboard")
        gestionnaire_group.permissions.set(app_permissions)

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@imacid-logistics.local", "admin123")
            self.stdout.write(self.style.SUCCESS("Compte 'admin' créé (mot de passe : admin123)."))
        else:
            self.stdout.write("Le compte 'admin' existe déjà.")

        if not User.objects.filter(username="gestionnaire").exists():
            u = User.objects.create_user("gestionnaire", "gestionnaire@imacid-logistics.local", "gestion123")
            u.is_staff = True
            u.save()
            u.groups.add(gestionnaire_group)
            self.stdout.write(self.style.SUCCESS("Compte 'gestionnaire' créé (mot de passe : gestion123)."))
        else:
            self.stdout.write("Le compte 'gestionnaire' existe déjà.")

        if not User.objects.filter(username="utilisateur").exists():
            u = User.objects.create_user("utilisateur", "utilisateur@imacid-logistics.local", "user123")
            u.groups.add(utilisateur_group)
            u.save()
            self.stdout.write(self.style.SUCCESS("Compte 'utilisateur' créé (mot de passe : user123)."))
        else:
            self.stdout.write("Le compte 'utilisateur' existe déjà.")
