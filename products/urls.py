from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.productsList, name="list"),
    path("add/", views.add_product, name="add"),
    path("<int:pk>/update/", views.update_product, name="update"),
    path("<int:pk>/delete/", views.delete_product, name="delete"),
    path("<int:pk>/", views.product_detail, name="detail"),
    path("panier/", views.voir_panier, name="panier"),
    path("panier/ajouter/<int:pk>/", views.ajouter_au_panier, name="ajouter_au_panier"),
    path("panier/modifier/<int:pk>/", views.modifier_quantite_panier, name="modifier_quantite_panier"),
    path("panier/retirer/<int:pk>/", views.retirer_du_panier, name="retirer_du_panier"),
    path("commander/", views.commander, name="commander"),
    path("commande/confirmation/<uuid:references>/", views.confirmation_commande, name="confirmation_commande")
]
