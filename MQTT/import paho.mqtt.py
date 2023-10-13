import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime


broker = "test.mosquitto.org"
topics = ["grjoj_infos"]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connexion établie avec succès")
        # Souscription aux topics
        for topic in topics:
            client.subscribe(topic)
    else:
        print("Échec de la connexion. Code de retour =", rc)

    
client = mqtt.Client()
client.on_connect = on_connect
# Connexion au broker MQTT
client.connect(broker, 1883, 60)
client.loop_forever()