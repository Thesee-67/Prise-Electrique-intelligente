from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

def index(request):
    return render(request, 'GRJOJAPP/index.html')

def capteur(request):
    return render(request, 'GRJOJAPP/Capteur_temperature/capteur.html')

def plage(request):
    return render(request, 'GRJOJAPP/plage_horaires/plage_horaire.html')

def etat(request):
    return render(request, 'GRJOJAPP/etat_prise/etat.html')