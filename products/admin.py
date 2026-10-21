from django.contrib import admin
from .models import Products,Commande,LigneCommande
# Register your models here.

@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prix",
        "stock",
        "tva",
        "actif",
        "date_creation",
    )
    list_filter = ("actif",)
    search_fields = ("name", "description")
    list_editable = ("prix", "stock", "actif")


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = (
        "product_name",
        "quantite",
        "prix_unitaire_ht",
        "taux_tva",
        "montant_ht",
        "montant_tva",
        "montant_ttc",
    )

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "references",
        "nom_client",
        "telephone",
        "statut",
        "total_ttc",
        "date_creation",
    )

    list_filter = ("statut",  "date_creation")
    search_fields = ("nom_client", "telephone", "adress")
    readonly_fields = (
        "references",
        "total_ht",
        "total_tva",
        "total_ttc",
        "date_creation",
    )

    inlines = [LigneCommandeInline]

@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "commande",
        "quantite",
        "montant_ttc",
    )

    readonly_fields = (
        "commande",
        "product",
        "product_name",
        "quantite",
        "prix_unitaire_ht",
        "taux_tva",
        "montant_ht",
        "montant_tva",
        "montant_ttc",
    )