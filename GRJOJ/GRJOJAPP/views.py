from django.shortcuts import render, redirect
from .models import Informations
from datetime import datetime, time
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
from .forms import PlageHoraireForm
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.urls import reverse
import smtplib

def index(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            if username == 'toto' and password == 'toto':
                return redirect('acceuil')
            else:
                login_url = reverse('index')
                message = 'Échec de la connexion. Vérifiez votre nom d\'utilisateur et mot de passe. <a href="{}">Revenir à la page de connexion</a>.'.format(login_url)
                return HttpResponse(message)
    else:
        form = LoginForm()

    return render(request, 'GRJOJAPP/index.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'GRJOJAPP/logout.html')  # Vous pouvez personnaliser cette page de déconnexion


def acceuil(request):
    return render(request, 'GRJOJAPP/acceuil.html')

broker = '192.168.50.62'
username = 'toto'
password = 'toto'
port = 1883
topic_infos = 'grjoj_infos'
topic_heures = 'grjoj_heures'
topic_reconnect = 'grjoj_reconnect'
topic_modes = 'grjoj_mod'

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe(topic_modes)
        client.subscribe(topic_reconnect)
    else:
        print(f"Connection failed with error code {rc}")

def on_disconnect(client, userdata, rc):
    print("\nDisconnected from MQTT broker")

def initialize_mqtt():
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.username_pw_set(username, password)
    client.connect(broker, port, 60)
    client.loop_start()  # Démarrez la boucle MQTT en arrière-plan

initialize_mqtt()

def select_prise(request):
    latest_information = Informations.objects.latest('id')
    if request.method == 'POST':
        selected_prise = request.POST.get('selected_prise')
        allumer_prises = request.POST.get('allumer_prises')
        eteindre_prises = request.POST.get('eteindre_prises')

        informations = Informations.objects.first() 

        if selected_prise == "prise1_on":
            informations.prise1 = "ON"
        elif selected_prise == "prise1_off":
            informations.prise1 = "OFF"
        elif selected_prise == "prise2_on":
            informations.prise2 = "ON"
        elif selected_prise == "prise2_off":
            informations.prise2 = "OFF"
        
        if allumer_prises == "on":
            informations.prise1 = "ON"
            informations.prise2 = "ON"
        elif eteindre_prises == "off":
            informations.prise1 = "OFF"
            informations.prise2 = "OFF"

        informations.save()
   
        return redirect('confirmation')
    else:
        informations = Informations.objects.first() 

    return render(request, 'GRJOJAPP/prise.html', {'informations': informations, 'latest_information':latest_information })


def plage_horaire(request):
    informations = Informations.objects.first()
    form = PlageHoraireForm(request.POST or None, instance=informations)
    latest_informations = Informations.objects.latest('id')

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            # Vérification de l'état actuel de la prise
            if informations.prise1 == "ON":
                informations.prise1 = "ON"
            if informations.prise2 == "ON":
                informations.prise2 = "ON"

            if start_time:
                start_time = datetime.strptime(start_time, '%H:%M:%S').time()
            if end_time:
                end_time = datetime.strptime(end_time, '%H:%M:%S').time()
            
            if not informations.startplage1:
                informations.startplage1 = time(0, 0, 0)
            if not informations.endplage1:
                informations.endplage1 = time(0, 0, 0)
            if not informations.startplage2:
                informations.startplage2 = time(0, 0, 0)
            if not informations.endplage2:
                informations.endplage2 = time(0, 0, 0)

            # Vérification de l'heure actuelle pour activer/désactiver les prises
            current_time = datetime.now().time()
            plage_horaire_prise1 = (informations.startplage1, informations.endplage1)
            plage_horaire_prise2 = (informations.startplage2, informations.endplage2)

            if plage_horaire_prise1[0] <= current_time <= plage_horaire_prise1[1]:
                informations.prise1 = "ON"
            if plage_horaire_prise2[0] <= current_time <= plage_horaire_prise2[1]:
                informations.prise2 = "ON"

            informations.save()
            return redirect('confirmation')

    return render(request, 'GRJOJAPP/plage_horaire.html', {'form': form,'latest_informations': latest_informations})

def Capteur(request):
    # Récupérez les données du capteur depuis la base de données
    latest_information = Informations.objects.latest('id')

    # Vérifiez si la température est supérieure à 25 degrés
    if latest_information.capteur1 > 25:
        # Configurez les détails de l'e-mail
        from_email = 'toto81839@gmail.com'
        to_email = 'og67guittet@gmail.com'
        subject = 'Alerte de température élevée'
        message = f'La température est de {latest_information.capteur1} degrés.'

        # Établissez une connexion SMTP
        smtp_server = 'smtp.gmail.com'  # Exemple pour Gmail, mettez à jour pour votre serveur
        smtp_port = 587
        smtp_username = 'toto81839@gmail.com'
        smtp_password = 'toto81839'

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Créez et envoyez l'e-mail
        email = f'Subject: {subject}\n\n{message}'
        server.sendmail(from_email, to_email, email)

        # Fermez la connexion SMTP
        server.quit()

        # Vérifiez si la température est supérieure à 25 degrés
    if latest_information.capteur2 > 25:
        # Configurez les détails de l'e-mail
        from_email = 'toto81839@gmail.com'
        to_email = 'og67guittet@gmail.com'
        subject = 'Alerte de température élevée'
        message = f'La température est de {latest_information.capteur2} degrés.'

        # Établissez une connexion SMTP
        smtp_server = 'smtp.gmail.com'  # Exemple pour Gmail, mettez à jour pour votre serveur
        smtp_port = 587
        smtp_username = 'toto81839@gmail.com'
        smtp_password = 'toto81839'

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Créez et envoyez l'e-mail
        email = f'Subject: {subject}\n\n{message}'
        server.sendmail(from_email, to_email, email)

        # Fermez la connexion SMTP
        server.quit()

    return render(request, 'GRJOJAPP/capteur.html', {'latest_information': latest_information})


def confirmation(request):
    # Récupérez l'état des prises 1 et 2 depuis la base de données
    informations = Informations.objects.first()
    prise1_state = informations.prise1 if informations.prise1 else "OFF"
    prise2_state = informations.prise2 if informations.prise2 else "OFF"

    startplage1 = informations.startplage1 if informations.startplage1 else "00:00:00"
    startplage2 = informations.startplage2 if informations.startplage2 else "00:00:00"
    endplage1 = informations.endplage1 if informations.endplage1 else "00:00:00"
    endplage2 = informations.endplage2 if informations.endplage2 else "00:00:00"

    # Formatez la réponse au format souhaité
    response = f"{prise1_state};{prise2_state};{startplage1};{endplage1};{startplage2};{endplage2}"

    # Publiez la réponse au format MQTT
    client.publish(topic_modes, response)

    return render(request, 'GRJOJAPP/Confirmation.html')

