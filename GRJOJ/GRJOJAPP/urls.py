from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("index/", views.index, name='index'),

#Capteur
    path('capteur/', views.capteur, name='capteur'),

#Plage Horaires
    path('plage_horaire/', views.plage_horaire, name='plage_horaire'),

#Commande Prise
    path('prise/', views.select_prise, name='prise'),
    path('acceuil/', views.acceuil, name='acceuil'),
    path('logout/', views.logout_view, name='logout'),
]