#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

/////////////////////////////////////////////
// CAMBIAR SOLO ESTO EN CADA ESP32
/////////////////////////////////////////////

// Cambiar el identificador del nodo
#define NODE_ID "nodo1"      // CAMBIAR: nodo1 / nodo2 / nodo3

// Topic de publicación
#define TOPIC_PUB "iot/ambiente/nodo1"   // CAMBIAR para cada nodo

// Topic de control
#define TOPIC_SUB "iot/control/nodo1"    // CAMBIAR para cada nodo

/////////////////////////////////////////////
// ACTIVAR / DESACTIVAR COMPONENTES
/////////////////////////////////////////////

#define USE_DHT true
#define USE_LDR true
#define USE_RELAY true

// WiFi
const char* ssid = "red emiliano";
const char* password = "202320082004";

// IP del Raspberry Pi (Broker MQTT)
const char* mqtt_server = "192.168.1.100"; // CAMBIAR

/////////////////////////////////////////////////
// PINES Cambiar a los que esten conectados
/////////////////////////////////////////////////

#define DHTPIN 4
#define DHTTYPE DHT22

#define LDR_PIN 34
#define RELAY_PIN 17

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

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

void callback(char* topic, byte* payload, unsigned int length) {
  String message;

  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Mensaje recibido: ");
  Serial.println(message);

  if (USE_RELAY) {
    if (message == "1") {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("Relevador ENCENDIDO");
    }

    if (message == "0") {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("Relevador APAGADO");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conexion MQTT...");
    String clientId = "ESP32-";
    clientId += NODE_ID;

    if (client.connect(clientId.c_str())) {

      Serial.println("conectado");

      client.subscribe(TOPIC_SUB);

    } else {
      Serial.print("Error, rc=");
      Serial.print(client.state());
      Serial.println(" intentando de nuevo en 5s");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);

  if (USE_RELAY) {
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);
  }

  if (USE_DHT) {
    dht.begin();
  }

  if (USE_LDR) {
    pinMode(LDR_PIN, INPUT);
  }

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

unsigned long lastMsg = 0;

void loop() {
  if (!client.connected()) {
    reconnect();
  }

  client.loop();

  unsigned long now = millis();

  if (now - lastMsg > 5000) {
    lastMsg = now;

    bool dht_ok = false;
    bool ldr_ok = false;
    bool relay_ok = false;

    float temperatura = -1.0;
    float humedad = -1.0;
    int ldr = -1;
    int luz = -1;

    if (USE_DHT) {
      temperatura = dht.readTemperature();
      humedad = dht.readHumidity();

      if (!isnan(temperatura) && !isnan(humedad)) {
        dht_ok = true;
      } else {
        Serial.println("Error leyendo DHT");
      }
    } else {
      dht_ok = false;
    }

    if (USE_LDR) {
      ldr = analogRead(LDR_PIN);

      if (ldr >= 0 && ldr <= 4095) {
        ldr_ok = true;
        luz = map(ldr, 0, 4095, 0, 100);
      } else {
        Serial.println("Error leyendo LDR");
      }
    } else {
      ldr_ok = false;
    }

    if (USE_RELAY) {
      relay_ok = true;
    } else {
      relay_ok = false;
    }

    String payload = "{";

    payload += "\"nodo\":\"";
    payload += NODE_ID;
    payload += "\",";

    payload += "\"dht_ok\":";
    payload += (dht_ok ? "true" : "false");
    payload += ",";

    payload += "\"ldr_ok\":";
    payload += (ldr_ok ? "true" : "false");
    payload += ",";

    payload += "\"relay_ok\":";
    payload += (relay_ok ? "true" : "false");
    payload += ",";

    payload += "\"temperatura\":";
    if (dht_ok) {
      payload += String(temperatura, 2);
    } else {
      payload += "null";
    }
    payload += ",";

    payload += "\"humedad\":";
    if (dht_ok) {
      payload += String(humedad, 2);
    } else {
      payload += "null";
    }
    payload += ",";

    payload += "\"luz\":";
    if (ldr_ok) {
      payload += String(luz);
    } else {
      payload += "null";
    }

    payload += "}";

    //////////////////////////////////////
    // PUBLICAR MQTT
    //////////////////////////////////////

    client.publish(TOPIC_PUB, payload.c_str());

    Serial.print("Publicado: ");
    Serial.println(payload);
  }
}