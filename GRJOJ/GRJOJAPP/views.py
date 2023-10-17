from django.shortcuts import render, redirect
from .models import Informations
import paho.mqtt.client as mqtt
from datetime import datetime, time
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
from .forms import PlageHoraireForm
import time

def index(request):
    # Récupérez l'état des prises 1 et 2 depuis la base de données
    informations = Informations.objects.first()
    prise1_state = informations.prise1 if informations.prise1 else "OFF"
    prise2_state = informations.prise2 if informations.prise2 else "OFF"

    startplage1 = informations.startplage1 if informations.startplage1 else "00:00:00"
    startplage2 = informations.startplage2 if informations.startplage2 else "00:00:00"
    endplage1 = informations.endplage1 if informations.endplage1 else "00:00:00"
    endplage2 = informations.endplage2 if informations.endplage2 else "00:00:00"

    other_values = "00.0;00.0"
    # Formatez la réponse au format souhaité
    response = f"{prise1_state};{prise2_state};{startplage1};{startplage2};{endplage1};{endplage2};{other_values}"

    # Publiez la réponse au format MQTT
    client.publish(topic_modes, response)

    return render(request, 'GRJOJAPP/index.html', {'informations': informations})

broker = '192.168.170.62'
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
    if request.method == 'POST':
        selected_prise = request.POST.get('selected_prise')

        informations = Informations.objects.first()

        if selected_prise == "prise1_on":
            informations.prise1 = "ON"
        elif selected_prise == "prise1_off":
            informations.prise1 = "OFF"
        elif selected_prise == "prise2_on":
            informations.prise2 = "ON"
        elif selected_prise == "prise2_off":
            informations.prise2 = "OFF"
        informations.save()

        # Publish selected_prise to MQTT topic
        client.publish(topic_modes, selected_prise)

        return redirect('index')

    return render(request, 'GRJOJAPP/prise.html')

def plage_horaire(request):
    informations = Informations.objects.first()
    form = PlageHoraireForm(request.POST or None, instance=informations)

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

            # Le reste de votre code ici
            client.publish(topic_infos, f"{start_time};{end_time}")
            time.sleep(1)
            
            # Vérification de l'heure actuelle pour activer/désactiver les prises
            current_time = datetime.now().time()
            plage_horaire_prise1 = (informations.startplage1, informations.endplage1)
            plage_horaire_prise2 = (informations.startplage2, informations.endplage2)

            if plage_horaire_prise1[0] <= current_time <= plage_horaire_prise1[1]:
                informations.prise1 = "ON"
            if plage_horaire_prise2[0] <= current_time <= plage_horaire_prise2[1]:
                informations.prise2 = "ON"

            informations.save()
            client.publish(topic_infos, f"{start_time};{end_time}")
            
            return redirect('index')

    return render(request, 'GRJOJAPP/plage_horaire.html', {'form': form})


