from django.db import models
from decimal import Decimal
import uuid
# Create your models here.
class Products(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock= models.PositiveIntegerField(default=0)
    tva = models.DecimalField(max_digits=10, decimal_places=2, default=19.25)
    photo = models.ImageField(upload_to="products/", blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateField(auto_now_add=True)

    @property
    def prix_ttc(self):
        coefficient = Decimal("1") + self.tva / Decimal("100")
        return (self.prix * coefficient).quantize(
            Decimal("0.01")
        )

    def __str__(self):
        return self.name


class Commande(models.Model):
    STATUT_CHOICES =[
        ("confirmer", "Confirmer"),
        ("annulee", "Annulee"),
    ]

    PAIEMENT_CHOICES = [
        ("livraison", "Paiemnt a la livraison"),
    ]

    references = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )


    nom_client = models.CharField(max_length=100)
    telephone = models.CharField(max_length=100)
    adress = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    statut= models.CharField(
        max_length=25,
        choices=STATUT_CHOICES,
        default="livraison",
    )

    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Commande {self.references}"


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes",)
    product = models.ForeignKey(Products, on_delete=models.PROTECT, related_name="lignes_commande",)
    product_name = models.CharField(max_length=100)
    quantite = models.PositiveIntegerField()
    prix_unitaire_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    montant_ht = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    montant_tva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    montant_ttc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantite}" f" - commande {self.commande.references}"