/*
 Basic ESP8266 MQTT example
 This sketch demonstrates the capabilities of the pubsub library in combination
 with the ESP8266 board/library.
 It connects to an MQTT server then:
  - publishes "hello world" to the topic "outTopic" every two seconds
  - subscribes to the topic "inTopic", printing out any messages
    it receives. NB - it assumes the received payloads are strings not binary
  - If the first character of the topic "inTopic" is an 1, switch ON the ESP Led,
    else switch it off
 It will reconnect to the server if the connection is lost using a blocking
 reconnect function. See the 'mqtt_reconnect_nonblocking' example for how to
 achieve the same result without blocking the main loop.
 To install the ESP8266 board, (using Arduino 1.6.4+):
  - Add the following 3rd party board manager under "File -> Preferences -> Additional Boards Manager URLs":
       http://arduino.esp8266.com/stable/package_esp8266com_index.json
  - Open the "Tools -> Board -> Board Manager" and click install for the ESP8266"
  - Select your ESP8266 in "Tools -> Board"
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>

#define EEPROM_SIZE 12

// Update these with values suitable for your network.

const char* ssid = "Hello";
const char* password = "Bonjour*'";
const char* mqtt_server = "test.mosquitto.org";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE	(50)
char msg[MSG_BUFFER_SIZE];
int value = 0;

String outTopic = "grjoj_infoR";
String inTopic = "grjoj_infoApp";

String outTopic2 = "grjoj_heureR";
String inTopic2 = "grjoj_heureS";

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
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  if (topic == inTopic) {
    ind1 = (char)payload[0].indexOf(';');
    Prise1 = (char)payload[0].substring(0, ind1);
    ind2 = (char)payload[0].indexOf(';', ind1+1);
    Prise2 = (char)payload[0].substring(ind1+1, ind2+1);
    ind3 = (char)payload[0].indexOf(';', ind2+1);
    StartPlage1 = (char)payload[0].substring(ind2+1, ind3+1);
    ind4 = (char)payload[0].indexOf(';', ind3+1);
    EndPlage1 = (char)payload[0].substring(ind3+1, ind4+1);
    ind5 = (char)payload[0].indexOf(';', ind4+1);
    StartPlage2 = (char)payload[0].substring(ind4+1, ind5+1);
    ind6 = (char)payload[0].indexOf(';', ind5+1);
    EndPlage2 = (char)payload[0].substring(ind5+1);
  
    if (Prise1 == "ON") {
      digitalWrite("Broche à alimenter", LOW);  
    } else {
      digitalWrite("Broche à couper", HIGH); 
    }
    if (Prise2 == "ON") {
      digitalWrite("Broche à alimenter", LOW);  
    } else {
      digitalWrite("Broche à couper", HIGH); 
    }
    msg1 = StartPlage1 + ";" + EndPlage1;
    client.publish(outTopic2, msg1);  
    msg2 = StartPlage2 + ";" + EndPlage2;
    client.publish(outTopic2, msg2);  
  } else if (topic == inTopic2) {
    ind7 = (char)payload[0].indexOf(';');
    heure1 = (char)payload[0].substring(0, ind7);
    ind8 = (char)payload[0].indexOf(';', ind7+1);
    heure2 = (char)payload[0].substring(ind7+1);

    if (heure1 == "YES") {
      digitalWrite("Broche à alimenter", LOW);  
    } else {
      digitalWrite("Broche à couper", HIGH); 
    }
    if (heure2 == "YES") {
      digitalWrite("Broche à alimenter", LOW);  
    } else {
      digitalWrite("Broche à couper", HIGH); 
    }
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
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish(outTopic, "hello app");
      client.publish(outTopic2, "hello script");
      // ... and resubscribe
      client.subscribe(inTopic);
      client.subscribe(inTopic2);
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
  pinMode(BUILTIN_LED, OUTPUT);     // Initialize the BUILTIN_LED pin as an output
  Serial.begin(115200);
  EEPROM.begin(EEPROM_SIZE)
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  Serial.print("Publish message: ");
  Serial.println(msg);
  client.publish(outTopic, msg);
}
