from django.urls import path

from . import views

urlpatterns = [
    path("index/", views.index),

#Capteur
    path('Capteur_temperature/capteur/', views.capteur),

#Plage Horaires
    path('plage_horaires/plage_horaire/', views.plage),

#Commande Prise
    path('etat_prise/etat/', views.etat),

]