from django import forms
from .models import Informations

class PlageHoraireForm(forms.ModelForm):
    class Meta:
        model = Informations
        fields = ['startplage1', 'endplage1', 'startplage2', 'endplage2']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe', 'autocomplete': 'off'}))

