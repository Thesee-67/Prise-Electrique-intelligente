#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#include <OneWire.h>
#include <DallasTemperature.h>
#define ONE_WIRE_BUS 14
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

const char* ssid = "Hello";
const char* password = "Bonjour*'";
const char* mqtt_server = "192.168.170.62";
const char* mqtt_username = "toto";
const char* mqtt_password = "toto";

WiFiClient espClient;
PubSubClient client(espClient);
String msg;
char msg_final[200];
int value = 0;

const char* topic_infos = "grjoj_infos";
const char* topic_mod = "grjoj_mod";
const char* topic_heures = "grjoj_heures";
const char* topic_capteurs = "grjoj_capteurs";
const char* topic_reconnect = "grjoj_reconnect";

String Prise1;
String Prise2;
String StartPlage1;
String EndPlage1;
String StartPlage2;
String EndPlage2;
String Capteur1;
String Capteur2;
String heure1;
String heure2;

int ind1;
int ind2;
int ind3;
int ind4;
int ind5;
int ind6;
int ind7;
int ind8;
int ind9;
int ind10;

const int buttonPin1 = 13;     
const int ledPin1 =  12;      

int lastButtonState;

unsigned long previousMillis = 0;
unsigned long interval = 1000;

void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  payload[length] = '\0';
  
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  if (strcmp(topic, topic_mod) == 0) {
    ind1 = message.indexOf(';');
    Prise1 = message.substring(0, ind1);
    ind2 = message.indexOf(';', ind1+1);
    Prise2 = message.substring(ind1+1, ind2+1);
    ind3 = message.indexOf(';', ind2+1);
    StartPlage1 = message.substring(ind2+1, ind3+1);
    ind4 = message.indexOf(';', ind3+1);
    EndPlage1 = message.substring(ind3+1, ind4+1);
    ind5 = message.indexOf(';', ind4+1);
    StartPlage2 = message.substring(ind4+1, ind5+1);
    ind6 = message.indexOf(';', ind5+1);
    EndPlage2 = message.substring(ind5+1);
    
  } else if (strcmp(topic, topic_heures) == 0) {
    ind7 = message.indexOf(';');
    heure1 = message.substring(0, ind7);
    ind8 = message.indexOf(';', ind7+1);
    heure2 = message.substring(ind7+1);

    if (heure1 == "YES") {
      Prise1 = "ON";
    } else {
      Prise1 = "OFF";
    }
    if (heure2 == "YES") {
      Prise2 = "ON";
    } else {
      Prise2 = "OFF";
    }

  } else if (strcmp(topic, topic_capteurs) == 0) {
    ind9 = message.indexOf(';');
    Capteur1 = message.substring(0, ind8);
    ind10 = message.indexOf(';', ind8+1);
    Capteur2 = message.substring(ind8+1);

  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_username)) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish(topic_reconnect, "YES");
      // ... and resubscribe
      client.subscribe(topic_mod);
      client.subscribe(topic_heures);
      client.subscribe(topic_capteurs);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(ledPin1, OUTPUT);
  pinMode(buttonPin1, INPUT);

  lastButtonState = digitalRead(buttonPin1);
  
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  sensors.begin();
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int buttonState = digitalRead(buttonPin1);

  if ((lastButtonState == LOW) and (buttonState)) {
    if (Prise1 == "ON") {
      Prise1 = "OFF";
    } else {
      Prise1 = "ON";
    }
  }

  lastButtonState = buttonState;

  if (Prise1 == "ON") {
    digitalWrite(ledPin1, HIGH);  
  } else {
    digitalWrite(ledPin1, LOW); 
  }

  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);
  Capteur1 = tempC;

  unsigned long currentMillis = millis();
   
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    msg = "";
    msg += (Prise1.length() > 0) ? Prise1 : "OFF";
    msg += ";";
    msg += (Prise2.length() > 0) ? Prise2 : "OFF";
    msg += ";";
    msg += (StartPlage1.length() > 0) ? StartPlage1 : "0:0:0";
    msg += ";";
    msg += (EndPlage1.length() > 0) ? EndPlage1 : "0:0:0";
    msg += ";";
    msg += (StartPlage2.length() > 0) ? StartPlage2 : "0:0:0";
    msg += ";";
    msg += (EndPlage2.length() > 0) ? EndPlage2 : "0:0:0";
    msg += ";";
    msg += (Capteur1.length() > 0) ? Capteur1 : "00,0";
    msg += ";";
    msg += (Capteur2.length() > 0) ? Capteur2 : "00,0";

    msg.toCharArray(msg_final, sizeof(msg_final));
    Serial.println("Publish message: ");
    Serial.println(msg_final);
    client.publish(topic_infos, msg_final);
  }
}
