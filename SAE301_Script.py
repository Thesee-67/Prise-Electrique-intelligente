import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import time

i = 0
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

broker = 'test.mosquitto.org'
port = 1883
topic_infos = 'grjoj_infos'
topic_heures = 'grjoj_heures'

client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe(topic_infos)
    else:
        print(f"Connection failed with error code {rc}")

def on_message(client, userdata, msg):
    global i
    i += 1
    data = msg.payload.decode()
    data_store = [a for a in data.split(";")]
    formatted_data_store = {}
    formatted_data_store[i] = []
    for item in data_store:
        try:
            formatted_data_store[i].append(float(item))
        except ValueError:
            formatted_data_store[i].append(item)
    print(f"Message received: {data}")

    mySql_insert_query = f"""
    INSERT INTO Informations 
    (Prise1, Prise2, StartPlage1, EndPlage1, StartPlage2, EndPlage2, Capteur1, Capteur2) 
    VALUES 
    ('{formatted_data_store[i][0]}', '{formatted_data_store[i][1]}', 
    '{formatted_data_store[i][2]}', '{formatted_data_store[i][3]}', '{formatted_data_store[i][4]}', 
    '{formatted_data_store[i][5]}', '{formatted_data_store[i][6]}', '{formatted_data_store[i][7]}')
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
    client.connect(broker, port, 60)
    client.loop_start()

    try:
        while True:
            heure()
            client.publish(topic_infos, "OFF;OFF;10:30:15;11:0:0;16:5:0;20:15:7;0;0")
            time.sleep(5)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()
    cursor.close()
    mydb.close()

if __name__ == '__main__':
    main()