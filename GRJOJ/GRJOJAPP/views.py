from django.shortcuts import render, redirect
from .models import Informations
import paho.mqtt.client as mqtt
from datetime import datetime, time
import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import time
from datetime import time

def index(request):
    # Récupérez l'état des prises 1 et 2 depuis la base de données
    informations = Informations.objects.first()
    prise1_state = informations.prise1 if informations.prise1 else "OFF"
    prise2_state = informations.prise2 if informations.prise2 else "OFF"

    # Initialisez toutes les autres valeurs à "0"
    other_values = "0:0:0;0:0:0;00,00;00,00"  # Modifier cela selon vos besoins

    # Formatez la réponse au format souhaité
    response = f"{prise1_state};{prise2_state};{other_values}"

    # Publiez la réponse au format MQTT
    client.publish(topic_modes, response)

    return render(request, 'GRJOJAPP/index.html')



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
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        informations = Informations.objects.first()
        informations.startplage1 = start_time
        informations.endplage1 = end_time
        informations.save()


        # Publish start_time and end_time to MQTT topic
        client.publish(topic_infos, f"{start_time};{end_time}")
        time.sleep(1)


    # Vérification de l'heure actuelle pour activer/désactiver les prises
    current_time = datetime.now().time()
    informations = Informations.objects.first()
    plage_horaire_prise1 = (informations.startplage1, informations.endplage1)
    plage_horaire_prise2 = (informations.startplage2, informations.endplage2)

    if plage_horaire_prise1[0] <= current_time <= plage_horaire_prise1[1]:
        informations.prise1 = "ON"
    else:
        informations.prise1 = "OFF"

    if plage_horaire_prise2[0] <= current_time <= plage_horaire_prise2[1]:
        informations.prise2 = "ON"
    else:
        informations.prise2 = "OFF"

    informations.save()

    return render(request, 'GRJOJAPP/plage_horaire.html')

