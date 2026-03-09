/*
=========================================
CONFIGURACION GENERAL
=========================================
Librerías necesarias:
WiFi
PubSubClient
DHT sensor library (Adafruit)
Adafruit Unified Sensor
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

/////////////////////////////////////////////
// CAMBIAR SOLO ESTO EN CADA ESP32
/////////////////////////////////////////////

// Cambiar el identificador del nodo
#define NODE_ID "nodo1"      // CAMBIAR: nodo1 / nodo2 / nodo3

/////////////////////////////////////////////

// WiFi
const char* ssid = "red emiliano";        // CAMBIAR
const char* password = "202320082004"; // CAMBIAR

// IP del Raspberry Pi (Broker MQTT)
const char* mqtt_server = "192.168.0.28"; // Debe coincidir con la API

// Topics MQTT construidos automaticamente con NODE_ID
char topic_pub[64];
char topic_sub[64];

/////////////////////////////////////////////////
// PINES Cambiar a los que esten conectados
/////////////////////////////////////////////////

#define DHTPIN 4 // Este
#define DHTTYPE DHT22

#define LDR_PIN 34 // Este

#define RELAY_PIN 17 // Este

/////////////////////////////////////////////////

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

/////////////////////////////////////////////////
// CONEXION WIFI
/////////////////////////////////////////////////

void setup_wifi() {

  delay(10);

  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

/////////////////////////////////////////////////
// CALLBACK MQTT (CONTROL RELEVADOR)
/////////////////////////////////////////////////

void callback(char* topic, byte* payload, unsigned int length) {

  String message;

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Mensaje recibido: ");
  Serial.println(message);

  if (message == "1") {
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("Relevador ENCENDIDO");
  }

  if (message == "0") {
    digitalWrite(RELAY_PIN, LOW);
    Serial.println("Relevador APAGADO");
  }
}

/////////////////////////////////////////////////
// RECONEXION MQTT
/////////////////////////////////////////////////

void reconnect() {

  while (!client.connected()) {

    Serial.print("Intentando conexion MQTT...");

    String clientId = "ESP32-";
    clientId += NODE_ID;

    if (client.connect(clientId.c_str())) {

      Serial.println("conectado");

      client.subscribe(topic_sub);

    } else {

      Serial.print("Error, rc=");
      Serial.print(client.state());
      Serial.println(" intentando de nuevo en 5s");

      delay(5000);
    }
  }
}

/////////////////////////////////////////////////
// SETUP
/////////////////////////////////////////////////

void setup() {

  Serial.begin(9600);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  dht.begin();

  setup_wifi();

  snprintf(topic_pub, sizeof(topic_pub), "iot/ambiente/%s", NODE_ID);
  snprintf(topic_sub, sizeof(topic_sub), "iot/control/%s", NODE_ID);

  Serial.print("TOPIC_PUB: ");
  Serial.println(topic_pub);
  Serial.print("TOPIC_SUB: ");
  Serial.println(topic_sub);

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

/////////////////////////////////////////////////
// LOOP
/////////////////////////////////////////////////

unsigned long lastMsg = 0;

void loop() {

  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  unsigned long now = millis();

  if (now - lastMsg > 5000) {

    lastMsg = now;

    //////////////////////////////////////
    // LEER SENSORES
    //////////////////////////////////////

    float temperatura = dht.readTemperature();
    float humedad = dht.readHumidity();

    int ldr = analogRead(LDR_PIN);
    int luz = map(ldr, 0, 4095, 0, 100);

    //////////////////////////////////////
    // VALIDAR DATOS
    //////////////////////////////////////

    if (isnan(temperatura) || isnan(humedad)) {

      Serial.println("Error leyendo DHT");
      return;
    }

    //////////////////////////////////////
    // CREAR JSON
    //////////////////////////////////////

    String payload = "{";

    payload += "\"nodo\":\"";
    payload += NODE_ID;
    payload += "\",";

    payload += "\"temperatura\":";
    payload += String(temperatura);
    payload += ",";

    payload += "\"humedad\":";
    payload += String(humedad);
    payload += ",";

    payload += "\"luz\":";
    payload += String(luz);

    payload += "}";

    //////////////////////////////////////
    // PUBLICAR MQTT
    //////////////////////////////////////

    client.publish(topic_pub, payload.c_str());

    Serial.print("Publicado: ");
    Serial.println(payload);
  }
}