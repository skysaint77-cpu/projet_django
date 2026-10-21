from django import forms
from .models import Products,Commande
from PIL import Image, UnidentifiedImageError

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = [
            "name",
            "description",
            "prix",
            "stock",
            "tva",
            "photo",
            "actif",
        ]

        widgets = {
            "name": forms.TelInput(attrs={
                "class": "form-control",
                "placeholder": "Ex. : Panier artisanal",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
            }),
            "prix": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
            }),
            "stock": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "tva": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "max": "100",
                "step": "0.01",
            }),
            "photo": forms.ClearableFileInput(attrs={
                "class": "form-control",
            })
        }

    def clean_prix(self):
        prix = self.cleaned_data["prix"]
        if prix <= 0:
            raise forms.ValidationError("Le prix doit etre superieur a zero.")

        return prix

    def clean_tva(self):
        tva = self.cleaned_data["tva"]
        if not 0 <= tva <= 100:
            raise forms.ValidationError("La tva doit etre comprise entre 0 et 100")
        return tva    


    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo or not getattr(photo, "committed", False):
            return photo

        if photo.size > 3 *1024 *1024:
            raise forms.ValidationError(
                "La photo ne doit pas depasser 3 Mo."
            )
        try:
            photo.seek(0)
            with Image.open(photo) as image:
                if image.format != "WEBP":
                    raise forms.ValidationError(
                        "Seules les images au format webp sont accepter"
                    )

                if image.width > 4000 or image.height > 4000:
                    raise forms.ValidationError(
                        "Les dimensions maximales sont de 4000 * 4000 pixels"
                    )
                image.verify()

        except forms.ValidationError:
            raise
        except (UnidentifiedImageError, OSError, ValueError):
            raise forms.ValidationError(
                "Le fichier fourni n'est pas une image valide"
            )
        finally:
            photo.seek(0)
        return photo



class CommandeForm(forms.ModelForm):
    class Meta:
        model=Commande
        fields=[
            "nom_client",
            "telephone",
            "adress",
            "ville",
            "notes",
        ]

        widgets = {
            "nom_client":forms.TextInput(attrs={
                "placeholder": "Nom complet",
                "class": "champ-formulaire",
            }),
            "telephone": forms.TextInput(attrs={
                "placeholder": "Ex. : 6xxxxxx",
                "class": "champ-formulaire,"
            }),
            "adress": forms.TextInput(attrs={
                "placeholder": "Quartier, rue, repere",
                "class": "champ-formulaire",
            }),
            "ville": forms.TextInput(attrs={
                "placeholder": "Ex. : Douala",
                "class": "champ-formulaire",
            }),
            "notes": forms.Textarea(attrs={
                "placeholder": "Instruction de livraison (facultatif)",
                "class": "champ-formulaire",
            }),
        }

    def clean_nom_client(self):
        nom = self.cleaned_data["nom_client"].strip()
        if len(nom) < 2:
            raise forms.ValidationError("Saisi un nom valide.")
        return nom


    def clean_telephone(self):
        telephone = self.cleaned_data["telephone"].strip()
        chiffres = "".join(c for c in telephone if c.isdigit())

        if len(chiffres) < 9 or len(chiffres) > 15:
            raise forms.ValidationError(
                "Saisis un numero de telephone valide."
            )
        return telephone