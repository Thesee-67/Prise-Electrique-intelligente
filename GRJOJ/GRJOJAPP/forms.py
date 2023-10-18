from django import forms
from .models import Informations

class PlageHoraireForm(forms.ModelForm):
    class Meta:
        model = Informations
        fields = ['startplage1', 'endplage1', 'startplage2', 'endplage2']
class LoginForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
