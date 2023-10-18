from django.urls import path

from . import views

urlpatterns = [
    path("index/", views.index, name='index'),

#Capteur
    #path('capteur/', views.capteur),

#Plage Horaires
    path('plage_horaire/', views.plage_horaire, name='plage_horaire'),

#Commande Prise
    path('prise/', views.select_prise, name='prise'),
    path('login/', views.login_view, name='login'),
]