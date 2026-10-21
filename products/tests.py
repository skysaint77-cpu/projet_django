from django.test import TestCase
from decimal import Decimal
from django.urls import reverse
from .models import Products,Commande,LigneCommande
# Create your tests here.

class TestsCommande(TestCase):
    def setUp(self):
        self.product = Products.objects.create(
            name="Vase artisanal",
            description = "Vase fabriquer a la main",
            prix = Decimal("1000.00"),
            stock= 5,
            tva = Decimal("19.25"),
            actif=True,
        )

        self.url_commande= reverse("products:commander")
        self.donnees_client = {
            "nom_client": "Jean Test",
            "telephone": "699123456",
            "adress": "Bonapriso, rue de test",
            "ville": "Douala",
            "notes": "",
        }


    def ajouter_au_panier(self, quantite):
        session = self.client.session
        session["panier"] = {
            str(self.product.pk): quantite,
        }
        session.save()


    def test_commande_valide_et_stock(self):
        self.ajouter_au_panier(2)

        response = self.client.post(
            self.url_commande,
            self.donnees_client,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Commande.objects.count(), 1)
        self.assertEqual(LigneCommande.objects.count(), 1)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

        commande = Commande.objects.first()
        self.assertEqual(
            commande.total_ht,
            Decimal("2000.00"),
        )
        self.assertEqual(
            commande.total_tva,
            Decimal("385.00"),
        )

        self.assertEqual(
            commande.total_ttc,
            Decimal("2385.00"),
        )

        self.assertEqual(
            self.client.session.get("panier", {}),
            {},
        )



    def test_panier_vide_refuse(self):
        response = self.client.post(
            self.url_commande,
            self.donnees_client,
        )  

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Commande.objects.count(), 0)
        self.assertEqual(LigneCommande.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)



    def test_stock_insuffisant_refuse(self):
        self.ajouter_au_panier(6)

        response = self.client.post(
            self.url_commande,
            self.donnees_client,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Commande.objects.count(), 0)
        self.assertEqual(LigneCommande.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_coordonnees_invalides_refuses(self):
        self.ajouter_au_panier(1)

        donnees_invalides=self.donnees_client.copy()
        donnees_invalides["nom_client"] = ""

        response = self.client.post(
            self.url_commande,
            donnees_invalides,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Commande.objects.count(), 0)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)