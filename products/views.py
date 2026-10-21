from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Products,Commande,LigneCommande
from .form import ProductForm,CommandeForm
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# Create your views here.

def productsList(request):
    products = Products.objects.filter(actif=True).order_by("-date_creation")
    recherche = request.GET.get("q","").strip()

    if recherche:
        products = products.filter(nom__incontains=recherche)
    return render(request, "products/list.html", {'products': products, 'recherche': recherche})


@staff_member_required
def add_product(request):
    if request.method == "POST":
        formulaire = ProductForm(
            request.POST,
            request.FILES,
        )

        if formulaire.is_valid():
            formulaire.save()
            return redirect("products:list")
    else:
        formulaire = ProductForm()
    return render(request, "products/formulaire.html", {
        "formulaire": formulaire,
        "titre": "Add a product",
    })

@staff_member_required
def update_product(request, pk):
    product = get_object_or_404(Products, pk=pk)

    if request.method == "POST":
        formulaire = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
        )

        if formulaire.is_valid():
            formulaire.save()
            return redirect("products:list")
    else:
        formulaire = ProductForm(instance=product)
    return render(request, "products/formulaire.html",{
        "formulaire": formulaire,
        "titre": "update a product",
    })


@staff_member_required
def delete_product(request, pk):
    product = get_object_or_404(Products, pk=pk)

    if request.method == "POST":
        product.delete()
        return redirect("products:list")

    return render(request, "products/confirm_delete.html",{
        "product":product,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Products,
        pk=pk,
        actif = True,
    )

    return render(
        request,
        "products/detail.html",
        {"product":product},
    )


def calculer_panier(request):
    panier = request.session.get("panier", {})
    lignes = []
    total_ht = Decimal("0.00")
    total_tva = Decimal("0.00")

    for product_id, quantite in panier.items():
        try:
            product = Products.objects.get(
                pk=int(product_id),
                actif=True,
            )
            quantite = int(quantite)
        except (ValueError, TypeError, Products.DoesNotExist):
            continue
        if quantite <= 0 or quantite > product.stock:
            continue
        montant_ht = product.prix * quantite
        montant_tva = (
            montant_ht * product.tva / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding = ROUND_HALF_UP,
        )
        montant_ttc = montant_ht + montant_tva

        lignes.append({
            "product": product,
            "quantite": quantite,
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
        })

        total_ht += montant_ht
        total_tva += montant_tva
    return {
        "lignes": lignes,
        "total_ht":total_ht,
        "total_tva": total_tva,
        "total_ttc": total_ht + total_tva,
    }


def voir_panier(request):
    contexte = calculer_panier(request)
    return render(request, "products/panier.html", contexte)


@require_POST
def ajouter_au_panier(request, pk):
    product = get_object_or_404(
        Products,
        pk=pk,
        actif=True,
    )
    try:
        quantite = int(request.POST.get("quantite", "1"))
    except (ValueError, TypeError):
        messages.error(request, "Quantite invalide")
        return redirect("products:detail", pk=pk)

    if quantite < 1:
        messages.error(request, "La quantite dois etre positive.")
        return redirect("products:detail", pk=pk)
    panier = request.session.get("panier", {})
    quantite_actuelle = int(panier.get(str(pk), 0))
    nouvelle_quantite = quantite_actuelle + quantite

    if nouvelle_quantite > product.stock:
        messages.error(
            request,
            f"stock insuffisant. Disponible : {product.stock}",
        )

        return redirect("products:detail", pk=pk)
    panier[str(pk)] = nouvelle_quantite
    request.session["panier"] = panier
    request.session.modified = True

    messages.success(request, "produit ajouter au panier")
    return redirect("products:panier")



@require_POST
def modifier_quantite_panier(request, pk):
    panier = request.session.get("panier", {})
    cle = str(pk)

    if cle not in panier:
        messages.error(request, "Produit absent du panier.")
        return redirect("products:panier")
    try:
        quantite = int(request.POST.get("quantite", "1"))
    except(ValueError, TypeError):
        return redirect("products:panier")

    product = get_object_or_404(
        Products,
        pk=pk,
        actif = True,
    )

    if quantite < 1:
        messages.error(request, "La quantite doit etre positive.")
    elif quantite > product.stock:
        messages.error(
            request,
            f"Stock insuffisant. Disponible : {product.stock}."
        )
    else:
        panier[cle] = quantite
        request.session["panier"] = panier
        request.session.modified = True
        messages.success(request, "Panier mise a jour .")
    return redirect("products:panier")


@require_POST
def retirer_du_panier(request, pk):
    panier = request.session.get("panier", {})
    panier.pop(str(pk), None)
    request.session["panier"] = panier
    request.session.modified = True

    return redirect("products:panier")


def commander(request):
    panier = request.session.get("panier", {})

    if not panier:
        messages.error(request, "Ton panier est vide.")
        return redirect("products:panier")

    if request.method == "POST":
        form = CommandeForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    commande = None
                    lignes_a_creer = []
                    total_ht = Decimal("0.00")
                    total_tva = Decimal("0.00")

                    for product_id, quantite_brut in panier.items():
                        try:
                            product_id = int(product_id)
                            quantite = int(quantite_brut)
                        except (ValueError, TypeError):
                            raise ValueError("Panier invalide.")
                        if quantite < 1:
                            raise ValueError("Quantite invalide.")
                        product = Products.objects.get(pk=product_id,actif=True,)
                        # if quantite > product.stock:
                        #     raise ValueError(
                        #         f"Stock insuffisant pour {product.name}."
                        #         f"Disponible : {product.stock}."
                        #     )
                        montant_ht = product.prix * quantite
                        montant_tva = (
                            montant_ht * product.tva / Decimal("100")
                        ).quantize(
                            Decimal("0.01"),
                            rounding=ROUND_HALF_UP,
                        )
                        montant_ttc = montant_ht + montant_tva
                        lignes_a_creer.append({
                            "product":product,
                            "product_name": product.name,
                            "quantite": quantite,
                            "prix_unitaire_ht": product.prix,
                            "taux_tva": product.tva,
                            "montant_ht": montant_ht,
                            "montant_tva": montant_tva,
                            "montant_ttc": montant_ttc
                        })

                        total_ht += montant_ht
                        total_tva +=montant_tva
                    commande = form.save(commit=False)
                    commande.total_ht = total_ht
                    commande.total_tva = total_tva
                    commande.total_ttc = total_ht + total_tva
                    commande.statut = "confirmee"
                    commande.mode_paiement = "livraison"
                    commande.save()

                    for ligne in lignes_a_creer:
                        product = ligne["product"]

                        LigneCommande.objects.create(
                            commande=commande,
                            **ligne,
                        )

                        product.stock -= quantite
                        product.save()

            except(ValueError, Products.DoesNotExist) as erreur:
                messages.error(request, str(erreur))
                return redirect("products:panier")
            request.session["panier"] ={}
            request.session.modified = True

            return redirect(
                "products:confirmation_commande",
                references = commande.references
            )
    else:
        form= CommandeForm()
        contexte={
            "form": form,
            "panier": panier,
        }
    if 'contexte' not in locals():
        contexte = {
            "form": form,
            "panier": panier,
        }
    return render(
        request, "products/commander.html",
            contexte
        )



def confirmation_commande(request, references):
    commande = get_object_or_404(
        Commande, references=references
    )

    return render(
        request, "products/confirmation_commande.html",{"commande": commande},
    )