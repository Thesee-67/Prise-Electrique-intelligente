#! /usr/bin/env python

import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import time

config = {
    'user':'client',
    'password':'secret',
    'host':'127.0.0.1',
    'database':'SAE301'
}

try:
    mydb = mysql.connector.connect(**config)
    cursor = mydb.cursor()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

broker = '192.168.170.62'
username = 'toto'
password = 'toto'
port = 1883
topic_infos = 'grjoj_infos'
topic_mod = 'grjoj_mod'
topic_heures = 'grjoj_heures'
topic_capteurs = 'grjoj_capteurs'
topic_reconnect = 'grjoj_reconnect'

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe(topic_infos)
        client.subscribe(topic_reconnect)
    else:
        print(f"Connection failed with error code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    data = msg.payload.decode()
    if topic == topic_reconnect:
        if data == "YES":
            mySql_pull_query = """
            SELECT Prise1, Prise2, StartPlage1, EndPlage1, StartPlage2, EndPlage2 
            FROM Informations
            ORDER BY id DESC LIMIT 1"""            
            cursor.execute(mySql_pull_query)
            infos = cursor.fetchone()
            if infos != None:
                client.publish(topic_mod, f"{infos}")
            else:
                client.publish(topic_mod, "OFF;OFF;0:0:0;0:0:0;0:0:0;0:0:0")
            mySql_pull_query = """
            SELECT Capteur1, Capteur2 
            FROM Informations
            ORDER BY id DESC LIMIT 1"""            
            cursor.execute(mySql_pull_query)
            infos = cursor.fetchone()
            if infos != None:
                client.publish(topic_capteurs, f"{infos}")
            else:
                client.publish(topic_capteurs, "00,0;00,0")
    elif topic == topic_infos:
        data_store = [a for a in data.split(";")]
        formatted_data_store = []
        for item in data_store:
            try:
                formatted_data_store.append(float(item))
            except ValueError:
                formatted_data_store.append(item)

        if len(formatted_data_store) == 8:
            print(f"Message received: {data}")
            mySql_insert_query = f"""
            INSERT INTO Informations 
            (Prise1, Prise2, StartPlage1, EndPlage1, StartPlage2, EndPlage2, Capteur1, Capteur2) 
            VALUES 
            ('{formatted_data_store[0]}', '{formatted_data_store[1]}', 
            '{formatted_data_store[2]}', '{formatted_data_store[3]}', '{formatted_data_store[4]}', 
            '{formatted_data_store[5]}', '{formatted_data_store[6]}', '{formatted_data_store[7]}')
            """
            
            cursor.execute(mySql_insert_query)
            mydb.commit()

def on_disconnect(client, userdata, rc):
    print("\nDisconnected from MQTT broker")

def heure():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    mySql_pull_query = """
    SELECT StartPlage1, EndPlage1, StartPlage2, EndPlage2 
    FROM Informations
    ORDER BY id DESC LIMIT 1"""            

    cursor.execute(mySql_pull_query)
    hours_tuple = cursor.fetchone()

    if hours_tuple is not None and (hours_tuple[0] != None) and (hours_tuple[1] != None) and (hours_tuple[2] != None) and (hours_tuple[3] != None):
        hours = ""
        for element in hours_tuple:
            hours = hours + str(element) + ";"

        hours_store = [a for a in hours.split(";")]
        StartPlage1 = hours_store[0]
        EndPlage1 = hours_store[1]
        StartPlage2 = hours_store[2]
        EndPlage2 = hours_store[3]

        if current_time > StartPlage1 and current_time < EndPlage1:
            hour1 = "YES"
        else:
            hour1 = "NO"

        if current_time > StartPlage2 and current_time < EndPlage2:
            hour2 = "YES"
        else:
            hour2 = "NO"

        client.publish(topic_heures, f"{hour1};{hour2}")
    else:
        print("No data found in the database")

def main():
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.username_pw_set(username, password)
    client.connect(broker, port, 60)
    client.loop_start()

    try:
        while True:
            heure()
            time.sleep(5)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()
    cursor.close()
    mydb.close()

if __name__ == '__main__':
    main()