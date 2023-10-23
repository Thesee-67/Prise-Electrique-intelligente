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
from django.core.mail import send_mail
import datetime

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

# Définissez des variables globales pour suivre le moment de la dernière alerte
last_alert_time1 = None
last_alert_time2 = None
threshold_temperature1 = 25.0  # Valeur par défaut pour capteur 1
threshold_temperature2 = 25.0  # Valeur par défaut pour capteur 2
threshold_temperature_critique = 40  # Seuil critique par défaut
delay = 3600  # Délai entre les alertes par défaut

def capteur(request):
    global last_alert_time1
    global last_alert_time2
    global threshold_temperature1
    global threshold_temperature2
    global threshold_temperature_critique
    global delay

    latest_information = Informations.objects.latest('id')
    temperature1 = float(latest_information.capteur1.replace(',', '.'))  # Remplacez la virgule par un point
    temperature2 = float(latest_information.capteur2.replace(',', '.'))  # Remplacez la virgule par un point

    # Récupérez les seuils de température à partir du formulaire
    if request.method == 'POST':
        new_threshold1 = float(request.POST.get('threshold_temperature1'))
        new_threshold2 = float(request.POST.get('threshold_temperature2'))
        new_threshold_critique = float(request.POST.get('threshold_temperature_critique'))
        new_delay = int(request.POST.get('delay_between_alerts'))

        # Vérifiez si les seuils ont été modifiés
        if new_threshold1 != threshold_temperature1 or new_threshold2 != threshold_temperature2:
            # Envoyez un e-mail pour informer de la modification des seuils
            subject = 'Modification des seuils de température'
            message = f'Nouveaux seuils : Capteur 1 : {new_threshold1}, Capteur 2 : {new_threshold2}'
            from_email = 'toto81839@gmail.com'  # Remplacez par votre adresse e-mail d'envoi
            recipient_list = ['og67guittet@gmail.com']  # Remplacez par l'adresse du destinataire
            password = 'jhgg rpce xjxm meoa'  # Utilisez le mot de passe d'application que vous avez généré

            # Envoyez l'e-mail en utilisant le mot de passe d'application
            send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_password=password)

        # Mettez à jour les seuils et le délai
        threshold_temperature1 = new_threshold1
        threshold_temperature2 = new_threshold2
        threshold_temperature_critique = new_threshold_critique
        delay = new_delay

    # Vérifiez si la température actuelle dépasse la température seuil pour capteur 1
    if temperature1 > threshold_temperature1:
        current_time = datetime.datetime.now()
        if last_alert_time1 is None or (current_time - last_alert_time1).total_seconds() >= delay:
            # Configurez les détails de l'e-mail
            subject = 'Alerte de température élevée'
            message = f'La température est supérieure à {threshold_temperature1}, la température actuelle est de {temperature1} degrés.'
            from_email = 'toto81839@gmail.com'  # Remplacez par votre adresse e-mail d'envoi
            recipient_list = ['og67guittet@gmail.com']  # Remplacez par l'adresse du destinataire
            password = 'jhgg rpce xjxm meoa'  # Utilisez le mot de passe d'application que vous avez généré

            # Envoyez l'e-mail en utilisant le mot de passe d'application
            send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_password=password)

            # Mettez à jour le moment de la dernière alerte
            last_alert_time1 = current_time

            if temperature1 > threshold_temperature_critique:
                # Si la température dépasse le seuil critique, envoyez un e-mail immédiatement
                subject = 'Alerte de température critique'
                message = f'La température est supérieure au seuil critique de {threshold_temperature_critique}, la température actuelle est de {temperature1} degrés.'
                from_email = 'toto81839@gmail.com'  # Remplacez par votre adresse e-mail d'envoi
                recipient_list = ['og67guittet@gmail.com']  # Remplacez par l'adresse du destinataire

                # Envoyez l'e-mail en utilisant le mot de passe d'application
                send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_password=password)

    # Vérifiez si la température actuelle dépasse la température seuil pour capteur 2
    if temperature2 > threshold_temperature2:
        current_time = datetime.datetime.now()
        if last_alert_time2 is None or (current_time - last_alert_time2).total_seconds() >= delay:
            # Configurez les détails de l'e-mail comme vous l'avez fait précédemment
            subject = 'Alerte de température élevée'
            message = f'La température est supérieure à {threshold_temperature2}, la température actuelle est de {temperature2} degrés.'
            from_email = 'toto81839@gmail.com'  # Remplacez par votre adresse e-mail d'envoi
            recipient_list = ['og67guittet@gmail.com']  # Remplacez par l'adresse du destinataire
            password = 'jhgg rpce xjxm meoa'  # Utilisez le mot de passe d'application que vous avez généré

            # Envoyez l'e-mail en utilisant le mot de passe d'application
            send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_password=password)

            # Mettez à jour le moment de la dernière alerte
            last_alert_time2 = current_time

            if temperature2 > threshold_temperature_critique:
                # Si la température dépasse le seuil critique, envoyez un e-mail immédiatement
                subject = 'Alerte de température critique'
                message = f'La température est supérieure au seuil critique de {threshold_temperature_critique}, la température actuelle est de {temperature2} degrés.'
                from_email = 'toto81839@gmail.com'  # Remplacez par votre adresse e-mail d'envoi
                recipient_list = ['og67guittet@gmail.com']  # Remplacez par l'adresse du destinataire

                # Envoyez l'e-mail en utilisant le mot de passe d'application
                send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_password=password)

    return render(request, 'GRJOJAPP/capteur.html', {
        'latest_information': latest_information,
        'threshold_temperature1': threshold_temperature1,
        'threshold_temperature2': threshold_temperature2,
        'threshold_temperature_critique': threshold_temperature_critique,
        'delay_between_alerts': delay,
    })


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

